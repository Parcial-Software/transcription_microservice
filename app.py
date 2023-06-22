import boto3
import json
import os
from deepgram import Deepgram
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS 


app = Flask(__name__)
CORS(app)

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Leer las variables de entorno
region_name = os.getenv("REGION_NAME")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
deepgram_key = os.getenv("DEEPGRAM_KEY")


@app.route("/transcriptions/<int:id>", methods=["GET"])
def get_transcription_by_id(id): 
    # Obtener el cliente de DynamoDB
    dynamodb = boto3.client(
        "dynamodb",
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    # Verificar si existe un elemento con el ID en la tabla
    get_response = dynamodb.get_item(
        TableName="transcriptions", Key={"id": {"N": str(id)}}
    )

    item = get_response.get("Item")

    if item:
        # Devolver el elemento encontrado en DynamoDB
        return jsonify(item)
    else:
        # Devolver un error 404
        return jsonify({"error": "Transcription not found"}), 404


@app.route("/transcriptions", methods=["POST"])
def create_transcription():
    # Obtener el contenido JSON del cuerpo de la solicitud
    data = request.get_json()

    # Obtener el cliente de DynamoDB
    dynamodb = boto3.client(
        "dynamodb",
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    # Verificar si existe un elemento con el ID en la tabla
    get_response = dynamodb.get_item(
        TableName="transcriptions", Key={"id": {"N": str(data["id"])}}
    )

    item = get_response.get("Item")

    if item:
        # Devolver el elemento encontrado en DynamoDB
        return jsonify(item)
    else:
        # Obtener las transcripciones utilizando Deepgram
        deepgram_transcriptions = get_transcriptions(data["data"])["results"]["channels"][0]["alternatives"][0]["paragraphs"]["paragraphs"]

        # Convertir el diccionario a JSON
        json_transcriptions = json.dumps({
            "transcript": "\n".join(sentence["text"] for paragraph in deepgram_transcriptions for sentence in paragraph["sentences"]),
            "sentences": [
                {
                    "start": sentence["start"],
                    "end": sentence["end"],
                    "text": sentence["text"]
                }
                for paragraph in deepgram_transcriptions
                for sentence in paragraph["sentences"]
            ]
        })

        # Realizar la inserción en la tabla "transcriptions"
        put_response = dynamodb.put_item(
            TableName="transcriptions",
            Item={"id": {"N": str(data["id"])}, "data": {"S": json_transcriptions}},
        )

        # Obtener el objeto insertado desde DynamoDB
        inserted_item = {
            "id": {"N": str(data["id"])},
            "data": {"S": json_transcriptions}
        }

        return jsonify(inserted_item)
    
@app.route("/transcriptions/<int:id>", methods=["DELETE"])
def delete_transcription_by_id(id):
    # Get the DynamoDB client
    dynamodb = boto3.client(
        "dynamodb",
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    # Delete the item from the "transcriptions" table
    response = dynamodb.delete_item(
        TableName="transcriptions",
        Key={"id": {"N": str(id)}}
    )

    # Check if the deletion was successful
    if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        return jsonify({"message": "Transcription deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete transcription"}), 500


def get_transcriptions(audio_link):
    # Configurar el cliente de Deepgram con tu token de autenticación
    client = Deepgram(deepgram_key)
    source = {"url": audio_link}
    options = {"smart_format": True, "tier": "enhanced"}
    response = client.transcription.sync_prerecorded(source, options)

    return response

if __name__ == '__main__':
    app.run()
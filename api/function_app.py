import logging
import json
import uuid
from datetime import datetime
import azure.functions as func

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.metrics_exporter import MetricsExporter
import os

# Instrumentation (au démarrage)
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
)

metrics_exporter = MetricsExporter(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

app = func.FunctionApp()

@app.function_name(name="post_user")
@app.route(route="user", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.cosmos_db_output(
    arg_name="outputDocument",
    database_name="bayroudb",
    container_name="users",
    connection="CosmosDBConnection",
    create_if_not_exists=True,
    partition_key="/email"
)
def post_user(req: func.HttpRequest, outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    logging.info("Processing POST /user")

    try:
        body = req.get_json()
        pseudo = body.get("pseudo") or body.get("email")
        email = body.get("email")

        if not pseudo or not email:
            return func.HttpResponse(
                json.dumps({"error": "Champs requis manquants : pseudo, email"}),
                mimetype="application/json",
                status_code=400
            )

        user_id = str(uuid.uuid4())
        document = {
            "id": str(uuid.uuid4()),    # clé primaire
            "email": email,             # partition key
            "pseudo": pseudo,
            "createdAt": datetime.utcnow().isoformat() + "Z"
}

        outputDocument.set(func.Document.from_dict(document))

        return func.HttpResponse(
            json.dumps({"status": "saved", "user": document}),
            mimetype="application/json",
            status_code=201
        )

    except Exception as e:
        logging.error(f"Erreur lors de l’insertion : {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
    


@app.function_name(name="post_vote")
@app.route(route="vote", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.cosmos_db_output(
    arg_name="outputDocument",
    database_name="bayroudb",
    container_name="votes",
    connection="CosmosDBConnection",
    create_if_not_exists=True,
    partition_key="/email"
)
def post_vote(req: func.HttpRequest, outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    logging.info("Processing POST /vote")

    try:
        body = req.get_json()
        email = body.get("email")
        choice = body.get("choice")

        if not email or not choice:
            return func.HttpResponse(
                json.dumps({"error": "Champs requis manquants : email, choice"}),
                mimetype="application/json",
                status_code=400
            )

        if choice not in ["Oui", "Non"]:
            return func.HttpResponse(
                json.dumps({"error": "Le choix doit être 'Oui' ou 'Non'"}),
                mimetype="application/json",
                status_code=400
            )

        # 👉 Vérification: tu peux utiliser le SDK ici si tu veux vraiment bloquer les doublons
        # mais pour l'instant on enregistre direct

        document = {
            "id": str(uuid.uuid4()),
            "email": email,
            "pseudo": email,  # ou récupéré depuis users si besoin
            "choice": choice,
            "createdAt": datetime.utcnow().isoformat() + "Z"
        }

        outputDocument.set(func.Document.from_dict(document))

        logger.info("New vote", extra={"custom_dimensions": {
        "choice": choice,
        "email": email
        }})

        return func.HttpResponse(
            json.dumps({"status": "saved", "vote": document}),
            mimetype="application/json",
            status_code=201
        )

    except Exception as e:
        logging.error(f"Erreur lors de l’insertion du vote : {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )





    

@app.function_name(name="get_votes")
@app.route(route="votes", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@app.cosmos_db_input(
    arg_name="votes",
    database_name="bayroudb",
    container_name="votes",
    connection="CosmosDBConnection",
    sql_query="SELECT c.email, c.pseudo, c.choice FROM c"
)
def get_votes(req: func.HttpRequest, votes: func.DocumentList) -> func.HttpResponse:
    logging.info("Processing GET /votes")

    try:
        # Convertir les documents en liste Python
        results = [doc.to_dict() for doc in votes]

        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Erreur lors de la récupération des votes : {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
    

# ============================
# GET /hasVoted?email=xxx
# ============================
@app.function_name(name="has_voted")
@app.route(route="hasVoted", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@app.cosmos_db_input(
    arg_name="votes",
    database_name="bayroudb",
    container_name="votes",
    connection="CosmosDBConnection",
    sql_query="SELECT * FROM c WHERE c.email = {email}"
)
def has_voted(req: func.HttpRequest, votes: func.DocumentList) -> func.HttpResponse:
    logging.info("Processing GET /hasVoted")

    try:
        email = req.params.get("email")
        if not email:
            return func.HttpResponse(
                json.dumps({"error": "Paramètre 'email' requis"}),
                mimetype="application/json",
                status_code=400
            )

        has_voted = len(votes) > 0
        return func.HttpResponse(
            json.dumps({"email": email, "hasVoted": has_voted}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Erreur lors de la vérification du vote : {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

@app.function_name(name="get_results")
@app.route(route="results", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@app.cosmos_db_input(
    arg_name="votes",
    database_name="bayroudb",
    container_name="votes",
    connection="CosmosDBConnection",
    sql_query="SELECT c.choice FROM c"
)
def get_results(req: func.HttpRequest, votes: func.DocumentList) -> func.HttpResponse:
    logging.info("Processing GET /results")

    try:
        results = {"Oui": 0, "Non": 0}
        for doc in votes:
            choice = doc.to_dict().get("choice")
            if choice in results:
                results[choice] += 1

        return func.HttpResponse(
            json.dumps(results),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Erreur lors du calcul des résultats : {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

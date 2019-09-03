import os
import json
import boto3
import logging

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)

client = boto3.client('lambda')

def lambda_handler(event, context):

    try:
        Filter = os.environ["Filter"]
    except:
        Filter = ""

    Marker = "First"
    FunctionList = []
    
    while True:

        if Marker == "First":
            response = client.list_functions(
                MaxItems=50
            )
        else:
            response = client.list_functions(
                Marker=Marker,
                MaxItems=50
            )

        try:
            Marker = response["NextMarker"]
        except:
            Marker = "Last"

        for Function in response["Functions"]:
            if Filter in Function["FunctionName"]:
                FunctionList.append(Function["FunctionName"])

        if Marker == "Last":
            break

    Marker = "First"
    LayerDict = {}

    while True:

        if Marker == "First":
            response = client.list_layers(
                CompatibleRuntime='python3.7',
                MaxItems=50
            )
        else:
            response = client.list_layers(
                CompatibleRuntime='python3.7',
                Marker=Marker,
                MaxItems=50
            )

        try:
            Marker = response["NextMarker"]
        except:
            Marker = "Last"

        for Layer in response["Layers"]:
            LayerDict[Layer["LayerName"]] = {
                "ARN": Layer["LatestMatchingVersion"]["LayerVersionArn"],
                "Version": Layer["LatestMatchingVersion"]["Version"]
            }

        if Marker == "Last":
            break
    
    for Function in FunctionList:

        logger.info(Function)
        
        FunctionResponse = client.get_function(
            FunctionName=Function
        )
    
        LayerList = []
        UpdateFlag = False

        if "Layers" in FunctionResponse["Configuration"]:
            FunctionARN = FunctionResponse["Configuration"]["FunctionArn"]

            for Layer in FunctionResponse["Configuration"]["Layers"]:
                LayerName = Layer["Arn"][0:Layer["Arn"].rfind(":")]
                LayerName = LayerName[LayerName.rfind(":")+1:]
                LayerVersion = int(Layer["Arn"][(Layer["Arn"].rfind(":")+1):])
                
                if LayerDict[LayerName]["Version"] > LayerVersion:
                    logger.info("Updated Needed: " + LayerName + " " + str(LayerVersion) + " < " + str(LayerDict[LayerName]["Version"]))
                    LayerList.append(LayerDict[LayerName]["ARN"])
                    UpdateFlag = True
                else:
                    logger.info("Up to date: " + LayerName + " " + str(LayerVersion) + " = " + str(LayerDict[LayerName]["Version"]))
                    LayerList.append(Layer["Arn"])
            
            if UpdateFlag:
                logger.info(LayerList)
                UpdateResponse = client.update_function_configuration(
                    FunctionName=FunctionARN,
                    Layers=LayerList
                )

                logger.info(UpdateResponse)
                
        
    return {}

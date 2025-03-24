from aws_cdk import (
    Stack,
)
from constructs import Construct
from aws_cdk.aws_apigatewayv2_integrations import HttpUrlIntegration, HttpLambdaIntegration
from aws_cdk import (
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_rds as rds,
    aws_iam as iam,
    aws_apigatewayv2 as apigwv2,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_ecs as ecs,
    aws_ecr as ecr,
)
import aws_cdk as cdk
from constructs import Construct

class BeStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        insert_inventory_fn = _lambda.Function(
            self, 'InsertInventory',
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset('lambda'),
            handler='insertInventory.lambda_handler',
        )
        get_inventory_fn = _lambda.Function(
            self, 'GetInventory',
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset('lambda'),
            handler='getInventory.lambda_handler',
        )
        table = dynamodb.TableV2(
            self, 'Inventory',
            partition_key=dynamodb.Attribute(name='pk', type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name='sk', type=dynamodb.AttributeType.STRING),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        table.add_global_secondary_index(
            index_name="skIndex",
            partition_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING)
        )
        table.add_global_secondary_index(
            index_name="dateIndex",
            partition_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name='updated_at', type=dynamodb.AttributeType.NUMBER),
        )
        # Grant UpdateItem permissions to the Lambda function
        table.grant(insert_inventory_fn, "dynamodb:UpdateItem")
        table.grant(get_inventory_fn, "dynamodb:Query")

        inventory_default_integration = HttpLambdaIntegration("InventoryIntegration", insert_inventory_fn)
        get_inventory_default_integration = HttpLambdaIntegration("GetInventoryIntegration", get_inventory_fn)

        http_api = apigwv2.HttpApi(self, "HttpApi",             
        cors_preflight=apigwv2.CorsPreflightOptions(
                allow_methods=[apigwv2.CorsHttpMethod.GET, apigwv2.CorsHttpMethod.POST],  # Allow GET and POST only
                allow_origins=["*"],  # Allow all origins
                allow_headers=["*"],  # Allow all headers
                expose_headers=["*"],  # Expose all headers
                max_age=cdk.Duration.days(10)  # Cache CORS response for 10 days
            )
        )
        
        # Add Authorizer Lambda
        authorizer_fn = _lambda.Function(
            self, 'ApiGatewayAuthorizer',
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset('lambda'),
            handler='apiGWAuthorizer.lambda_handler',
        )

        # # Create HTTP API Authorizer
        # authorizer = apigwv2.HttpAuthorizer(
        #     self, "HttpAuthorizer",
        #     authorizer_type=apigwv2.HttpAuthorizerType.LAMBDA,
        #     identity_source=['$request.header.Authorization'],
        #     authorizer_name="LambdaAuthorizer",
        #     handler=authorizer_fn
        # )

        # # Update route options to include authorizer
        # route_options = apigwv2.HttpRouteAuthorizerConfig(
        #     authorizer=authorizer,
        #     authorizer_type=apigwv2.HttpAuthorizerType.LAMBDA
        # )

        # Update existing routes with authorizer
        http_api.add_routes(
            path="/items",
            methods=[apigwv2.HttpMethod.GET],
            integration=get_inventory_default_integration,
            # authorizer=route_options
        )
        http_api.add_routes(
            path="/items",
            methods=[apigwv2.HttpMethod.POST],
            integration=inventory_default_integration,
            # authorizer=route_options
        )

        # Use default VPC
        vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

        # Create ECS Cluster
        cluster = ecs.Cluster(self, "MeiliCluster", vpc=vpc)

        # Define security group to allow port 7700
        sg = ec2.SecurityGroup(
            self, "MeiliSG", vpc=vpc,
            description="Allow access to Meilisearch",
            allow_all_outbound=True,
        )
        sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(7700),
            description="Allow Meilisearch HTTP access",
        )
        repo = ecr.Repository(self, "MeiliEcrRepo", repository_name="meilisearch-init")
        container_image = ecs.ContainerImage.from_ecr_repository(repo, tag="latest")
        task_def = ecs.FargateTaskDefinition(self, "MeiliTaskDef")
        container = task_def.add_container(
            "MeiliContainer",
            image=container_image,
            environment={"MEILI_MASTER_KEY": "MASTER_KEY"},
            logging=ecs.LogDrivers.aws_logs(stream_prefix="meili"),
        )
        container.add_port_mappings(ecs.PortMapping(container_port=7700))
        ecs.FargateService(self, "MeiliService",
            cluster=cluster,
            task_definition=task_def,
            security_groups=[sg],
            assign_public_ip=True,
            desired_count=1
        )


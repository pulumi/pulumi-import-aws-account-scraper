import boto3
import stringcase
from pprint import pprint
import json

translation_table = str.maketrans({' ': '_',
                                   '(': '_',
                                   ')': '_',
                                   '/': '_'})

def generate_import_resources(
    get_aws_resources,
    get_resource_id,
    pulumi_type_identifier
):
    pulumi_resources = []
    for aws_resource in get_aws_resources():
        resource_id = get_resource_id(aws_resource)

        name = f"import-{resource_id}"

        if "Name" in aws_resource:
            # Assuming that a Name attribute must be unique, e.g. for an S3
            # bucket.
            name = aws_resource["Name"]
        elif "Tags" in aws_resource:
            for tag in aws_resource["Tags"]:
                if tag["Key"] == "Name":
                    # Name tag values have no unique requirement, and thus need
                    # the ID appended to ensure uniqueness.
                    name = f"{tag['Value']}-{resource_id}"
                    break

        pulumi_resources.append({
            "type": pulumi_type_identifier,
            "name": name.translate(translation_table),
            "id": resource_id,
        })

    return pulumi_resources


def import_ec2_resources(resource_type_snake_case, ec2_client):
    resource_type_pascal_case = stringcase.pascalcase(resource_type_snake_case)
    resource_type_camel_case = stringcase.camelcase(resource_type_snake_case)

    get_aws_resources = (lambda: getattr(
        ec2_client, f"describe_{resource_type_snake_case}s")()[f"{resource_type_pascal_case}s"])
    get_resource_id = (
        lambda resource: resource[f"{resource_type_pascal_case}Id"])
    pulumi_type_identifier = f"aws:ec2/{resource_type_camel_case}:{resource_type_pascal_case}"

    return generate_import_resources(get_aws_resources, get_resource_id, pulumi_type_identifier)


def import_route_table_associations(ec2_client):
    pulumi_resources = []

    route_tables = ec2_client.describe_route_tables()['RouteTables']

    for route_table in route_tables:
        for association in route_table["Associations"]:
            if 'SubnetId' not in association:
                continue
            pulumi_resources.append({
                "type": "aws:ec2/routeTableAssociation:RouteTableAssociation",
                "name": f"import-{association['RouteTableAssociationId']}",
                "id": f"{association['SubnetId']}/{route_table['RouteTableId']}",
            })

    return pulumi_resources

def get_ec2_instances():
    reservations = ec2_client.describe_instances()["Reservations"]
    instances = []

    # reservations can be 0-n
    for reservation in reservations:
        instances.extend(reservation["Instances"])

    return instances

ec2_client = boto3.client('ec2')
pulumi_import = {
    "resources": []
}

resource_types = [
    'vpc',
    'subnet',
    'route_table',
    'nat_gateway',
    'internet_gateway',
]

for resource_type in resource_types:
    pulumi_import['resources'] += import_ec2_resources(
        resource_type, ec2_client)

# These don't follow the pattern:
pulumi_import['resources'] += import_route_table_associations(ec2_client)

pulumi_import['resources'] += generate_import_resources(
    lambda: ec2_client.describe_addresses()["Addresses"],
    lambda resource: resource["AllocationId"],
    "aws:ec2/eip:Eip",
)

pulumi_import['resources'] += generate_import_resources(
    lambda: get_ec2_instances(),
    lambda resource: resource["InstanceId"],
    "aws:ec2/instance:Instance",
)

pulumi_import['resources'] += generate_import_resources(
    lambda: ec2_client.describe_security_groups()["SecurityGroups"],
    lambda resource: resource["GroupId"],
    "aws:ec2/securityGroup:SecurityGroup",
)


print(json.dumps(pulumi_import, indent=2))

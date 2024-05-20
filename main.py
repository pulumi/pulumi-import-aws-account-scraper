import boto3
import json
import inflection
import wordninja

TYPES_TO_IGNORE = [
    'ec2:security-group-rule'
]


def map_resource_type_to_pulumi_type(resource_type):
    if resource_type == 'logs:log-group':
        return 'aws:cloudwatch/logGroup:LogGroup'

    namespace, resource_name = resource_type.split(':')

    resource_name_words = wordninja.split(resource_name)
    resource_name_underscores = '_'.join(resource_name_words)
    resource_name_camel_case = inflection.camelize(
        resource_name_underscores, False)
    resource_name_pascal_case = inflection.camelize(
        resource_name_underscores, True)

    pulumi_type = f"aws:{namespace}/{resource_name_camel_case}:{resource_name_pascal_case}"

    print(f'resource_type = {resource_type}, pulumi_type = {pulumi_type}')

    return pulumi_type


def main():
    client = boto3.client('resource-explorer-2')

    resources = []
    next_token = None

    while True:
        if next_token:
            response = client.search(QueryString='', NextToken=next_token)
        else:
            response = client.search(QueryString='')

        resources.extend(response['Resources'])

        if 'NextToken' in response:
            next_token = response['NextToken']
        else:
            break

    pulumi_resources = []
    resources_out_of_region = 0
    resources_ignored_by_type = 0

    cur_region = boto3.session.Session().region_name

    for resource in resources:
        if ('log-group' in resource['ResourceType'].lower()):
            print(resource)

        if resource['Region'] != cur_region:
            resources_out_of_region += 1
            continue

        if resource['ResourceType'] in TYPES_TO_IGNORE:
            print(f'Ignoring resource of type "{resource["ResourceType"]}"')
            resources_ignored_by_type += 1
            continue

        resource_type = resource['ResourceType']
        pulumi_type = map_resource_type_to_pulumi_type(resource_type)

        if resource['ResourceType'] in ['memorydb:parametergroup', 'elasticache:parametergroup']:
            segments = resource['Arn'].split(':')
            resource_id = segments[len(segments) -
                                   1].replace(':', '-').replace('/', '-').replace('.', '-')
        elif resource['ResourceType'] in ['logs:log-group']:
            segments = resource['Arn'].split(':')
            last_segment = segments[len(segments) - 1]
            resource_id = last_segment[1:].replace('/', '-')
        elif ('/' in resource['Arn']):
            segments = resource['Arn'].split('/')
            resource_id = segments[len(segments) - 1]
        elif ('.' in resource['Arn']):
            segments = resource['Arn'].split('.')
            resource_id = segments[len(segments) - 1]
        else:
            resource_id = resource['Arn']

        pulumi_resource = {
            "type": pulumi_type,
            "id": resource_id,
            "name": resource_id
        }

        pulumi_resources.append(pulumi_resource)

    pulumi_import = {
        "resources": pulumi_resources
    }

    with open('resources.json', 'w') as file:
        json.dump(pulumi_import, file, indent=2)

    print(f'{len(resources)} resources found in AWS Resource Explorer.')
    print(f'{resources_out_of_region} resources skipped because they are in a different region.')
    print(f'{resources_ignored_by_type} resources in this region skipped because they are of a type that cannot be easily imported (e.g. Security Group Rules)')
    print(f'{len(pulumi_resources)} Resources exported to resources.json.')


if __name__ == '__main__':
    main()

# pulumi-import-aws-account-scraper

This repo contains a sample Python script that uses the AWS Python SDK, [boto3](https://pypi.org/project/boto3/), to query resources in an AWS account/region and generate JSON suitable for the [`pulumi import`](https://www.pulumi.com/docs/reference/cli/pulumi_import/) command. It's intended as a starting point for organizations looking to import numerous resources that were created in the AWS console or via other IaC tools into Pulumi.

The code will query the following resource types:

- VPCs
- Subnets
- Routes
- Route tables
- Route table associations
- NAT gateways
- Internet gateways
- Elastic IPs
- Security groups
- EC2 instances

While this script is not a comprehensive solution, it should serve as a good and extensible starting point for organizations that are looking to move large numbers of resources into Pulumi.

To generate a JSON file for use with Pulumi import, run the following commands. Your AWS CLI credentials must be configured:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python account_scraper.py > ../path/to/file.json
```

To use the generated JSON file, run a command similar to the following from an existent Pulumi program's main directory:

```bash
pulumi import -f ../path/to/file -o imported-resources.ts -y
```

Substitute the output file in the command above with the appropriate file name and extension for your Pulumi program.

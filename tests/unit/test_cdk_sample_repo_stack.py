import aws_cdk as core
import aws_cdk.assertions as assertions

from azure_pipelines.load_env.config import CDKConfig
from cdk_sample_repo.cdk_sample_repo_stack import CdkSampleRepoStack


class TestCdkSampleRepoStack:
    def setup(self):
        self.app = core.App()
        self.config = CDKConfig("developer")
        self.stack = CdkSampleRepoStack(
            self.app, "cdk-sample-stack", config=self.config, stage="developer"
        )
        self.template = assertions.Template.from_stack(self.stack)

    def test_s3_bucket_created(self):
        """Test that an S3 bucket is created with proper encryption."""
        self.template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "BucketEncryption": {
                    "ServerSideEncryptionConfiguration": [
                        {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}
                    ]
                },
            },
        )

    def test_s3_bucket_security_settings(self):
        """Test that the S3 bucket has proper security settings."""
        self.template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True,
                },
                "VersioningConfiguration": {"Status": "Enabled"},
            },
        )

    def test_s3_bucket_ssl_enforcement(self):
        """Test that the S3 bucket enforces SSL."""
        self.template.has_resource_properties(
            "AWS::S3::BucketPolicy",
            {
                "PolicyDocument": {
                    "Statement": assertions.Match.array_with(
                        [
                            assertions.Match.object_like(
                                {
                                    "Action": "s3:*",
                                    "Condition": {
                                        "Bool": {"aws:SecureTransport": "false"}
                                    },
                                    "Effect": "Deny",
                                }
                            )
                        ]
                    )
                }
            },
        )

    def test_kms_key_created(self):
        """Test that a KMS key is created with proper configuration."""
        self.template.has_resource_properties(
            "AWS::KMS::Key",
            {
                "Description": "This key is used for encrypting contents of MyBucket",
                "Enabled": True,
                "EnableKeyRotation": True,
            },
        )

    def test_kms_key_alias(self):
        """Test that the KMS key has the correct alias."""
        self.template.has_resource_properties(
            "AWS::KMS::Alias",
            {"AliasName": "alias/BucketKey/MyBucketSampleRepo"},
        )

    def test_resource_count(self):
        """Test that the expected number of resources are created."""
        # Count resources by type
        self.template.resource_count_is("AWS::S3::Bucket", 1)
        self.template.resource_count_is("AWS::KMS::Key", 1)
        self.template.resource_count_is("AWS::KMS::Alias", 1)

    def test_nag_suppressions(self):
        """Test that CDK-NAG suppressions are applied."""
        # This is a metadata test - checking that the suppression is applied
        self.template.has_resource(
            "AWS::S3::Bucket",
            {
                "Metadata": assertions.Match.object_like(
                    {
                        "cdk_nag": {
                            "rules_to_suppress": assertions.Match.array_with(
                                [
                                    assertions.Match.object_like(
                                        {
                                            "id": "AwsSolutions-S1",
                                            "reason": "This bucket does not hold customer data",
                                        }
                                    )
                                ]
                            )
                        }
                    }
                )
            },
        )

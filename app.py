#!/usr/bin/env python3
"""CDK Sample Repository application."""

import asyncio
import os
from typing import Dict, List

import cdk_nag
from aws_cdk import Aspects, DefaultStackSynthesizer, Environment, Stack, Tags
from aws_pdk.cdk_graph import CdkGraph, FilterPreset
from aws_pdk.cdk_graph_plugin_diagram import CdkGraphDiagramPlugin
from aws_pdk.cdk_graph_plugin_threat_composer import CdkGraphThreatComposerPlugin
from aws_pdk.pdk_nag import PDKNagApp

from azure_pipelines.load_env.config import CDKConfig
from cdk_sample_repo.cdk_sample_repo_stack import CdkSampleRepoStack


class CdkSampleRepo(PDKNagApp):
    """Create the CDK App for network management."""

    def __init__(self, *args, **kwargs):
        """Initialize the CDK application."""
        super().__init__(*args, **kwargs)

        # Load configuration
        self.environment = self.node.try_get_context("environment")
        self.config = CDKConfig(self.environment)

        # Set up default synthesizer and environment
        self.default_synthesizer = DefaultStackSynthesizer(
            file_assets_bucket_name="mrht-cdk-bucket-assets-${AWS::AccountId}-${AWS::Region}",
            image_assets_repository_name="mrht-cdk-repository",
        )

        self.default_env = Environment(
            account=self.config.get_value("AccountId"),
            region=self.config.get_value("AWSRegion"),
        )

        # Initialize stack tracking
        self.stacks: List[Stack] = []
        self.stack_names: List[str] = []
        self.tags: Dict[str, str] = {}

    def create_tags(self) -> None:
        """Create default tags for all CDK resources."""
        branch_name = os.getenv("BUILD_SOURCEBRANCHNAME", "master")
        branch_name = "master" if branch_name == "merge" else branch_name

        self.tags = {
            "DeploymentMethod": "CDK - Python",  # Fixed typo in DeploymentMethod
            "CICD": "True",
            "RepositoryName": os.getenv("BUILD_REPOSITORY_NAME", "local"),
            "Environment": self.environment,
            "BranchName": branch_name,
            "Name": "Network Management Repo",
        }

    def create_cfn_stacks(self) -> None:
        """Create CloudFormation stacks."""
        stack_name = f"mrht-{self.environment}-sample-stack"

        sample_stack = CdkSampleRepoStack(
            self,
            construct_id="CdkSampleRepoStack",
            stack_name=stack_name,
            description="Dieser Cloudformation Stack erzeugt den Sample Stack.",
            env=self.default_env,
            config=self.config,
            synthesizer=self.default_synthesizer,
            stage=self.environment,
        )

        self.stacks.append(sample_stack)
        self.stack_names.append(stack_name)

        # Example of stack dependencies (commented out)
        # sample_stack.add_dependency(other_stack)

    def assign_tags(self) -> None:
        """Assign tags to all CloudFormation stacks."""
        for stack in self.stacks:
            for key, value in self.tags.items():
                Tags.of(stack).add(key, value)


async def main() -> None:
    """Run the CDK application asynchronously."""
    # Initialize the app
    app = CdkSampleRepo()

    # Add AWS Solutions Checks
    Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(verbose=True))

    # Set up CDK Graph for visualization
    graph = CdkGraph(
        app,
        plugins=[
            CdkGraphThreatComposerPlugin(
                application_details={
                    "name": "applications",
                }
            ),
            CdkGraphDiagramPlugin(
                diagrams=[
                    {
                        "name": "diagram",
                        "title": "Diagram CdkSampleRepoStack",
                        # "theme": "dark",
                        "filterPlan": {
                            "preset": FilterPreset.NON_EXTRANEOUS,
                        },
                    }
                ]
            ),
        ],
    )

    # Create and configure the application
    app.create_tags()
    app.create_cfn_stacks()
    app.assign_tags()

    # Synthesize the CloudFormation templates
    app.synth()

    # Generate the infrastructure diagram
    graph.report()


if __name__ == "__main__":
    asyncio.run(main())

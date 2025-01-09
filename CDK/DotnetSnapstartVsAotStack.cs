using System.Collections.Generic;
using Amazon.CDK;
using Amazon.CDK.AWS.Lambda;
using Constructs;

namespace CDK;

public class DotnetSnapstartVsAotStack : Stack
{
    internal DotnetSnapstartVsAotStack(Construct scope, string id, IStackProps props = null)
        : base(scope, id, props)
    {
        var function = new Function(
            this,
            "LambdaNet8Function",
            new FunctionProps
            {
                FunctionName = $"{Aws.STACK_NAME}-LambdaNet8",
                Runtime = Runtime.DOTNET_8,
                MemorySize = 1024,
                Timeout = Duration.Seconds(30),
                Handler = "LambdaNet8::" +
                          "LambdaNet8.Function::" +
                          "FunctionHandler",
                Code = Code.FromAsset("bin/LambdaNet8.zip"),
                Tracing = Tracing.ACTIVE
            });

        // SnapStart is not yet supported in the CDK
        ((CfnFunction)function.Node.DefaultChild)!.AddPropertyOverride(
            "SnapStart", new Dictionary<string, object>
            {
                { "ApplyOn", "PublishedVersions" }
            });

        var publishedVersion = new Version_(this, "LambdaNet8FunctionSnapStartVersion", new VersionProps
        {
            Lambda = function
        });

        new Alias(this, "LambdaNet8FunctionProdAlias", new AliasProps
        {
            AliasName = "SnapStart",
            Version = publishedVersion
        });

        new Function(
            this,
            "LambdaNet8AotFunction",
            new FunctionProps
            {
                FunctionName = $"{Aws.STACK_NAME}-LambdaNet8Aot",
                Runtime = Runtime.PROVIDED_AL2023,
                MemorySize = 1024,
                // The Handler property is set to "unused" to avoid the following error:
                // "Missing required properties for aws-cdk-lib.aws_lambda.FunctionProps: 'handler'"
                Handler = "unused",
                Code = Code.FromAsset("bin/LambdaNet8Aot.zip"),
                Tracing = Tracing.ACTIVE,
            });
    }
}
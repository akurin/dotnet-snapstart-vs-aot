using System.Text.Json.Serialization;

namespace LambdaNet8Aot;

[JsonSerializable(typeof(string))]
public partial class LambdaJsonSerializerContext : JsonSerializerContext;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;
using SAM.API;
using SAM.API.Callbacks;
using SAM.API.Types;

namespace GameHelper.SamHelper
{
    internal static class Program
    {
        private static int Main(string[] args)
        {
            try
            {
                if (args.Length < 2 || !long.TryParse(args[1], out var appId))
                {
                    WriteJson(new { ok = false, error = "Usage: GameHelper.SamHelper.exe list|set|clear <appid> [achievementId]" });
                    return 2;
                }

                var command = args[0].ToLowerInvariant();
                using var client = new Client();
                client.Initialize(appId);
                WaitForStats(client);

                if (command == "list")
                {
                    var achievements = LoadAchievements(client, appId, GetSteamPath(args));
                    WriteJson(new
                    {
                        ok = true,
                        appid = appId,
                        total = achievements.Count,
                        unlocked = achievements.Count(item => item.IsAchieved),
                        achievements,
                    });
                    return 0;
                }

                if (command == "states" && args.Length >= 3)
                {
                    var states = new List<AchievementDto>();
                    foreach (var id in args.Skip(2))
                    {
                        if (!client.SteamUserStats.GetAchievementAndUnlockTime(id, out var achieved, out var unlockTime))
                        {
                            continue;
                        }
                        states.Add(new AchievementDto
                        {
                            Id = id,
                            Name = id,
                            Description = "",
                            IsAchieved = achieved,
                            UnlockTime = achieved && unlockTime > 0 ? unlockTime : 0,
                        });
                    }
                    WriteJson(new { ok = true, appid = appId, achievements = states });
                    return 0;
                }

                if ((command == "set" || command == "clear") && args.Length >= 3)
                {
                    var id = args[2];
                    var state = command == "set";
                    if (!client.SteamUserStats.SetAchievement(id, state))
                    {
                        throw new InvalidOperationException("Steam не принял изменение достижения. Игра может блокировать локальное управление этим достижением.");
                    }
                    if (!client.SteamUserStats.StoreStats())
                    {
                        throw new InvalidOperationException("Steam не сохранил изменения достижений.");
                    }
                    WriteJson(new { ok = true, appid = appId, id, achieved = state });
                    return 0;
                }

                WriteJson(new { ok = false, error = "Unknown command." });
                return 2;
            }
            catch (Exception error)
            {
                WriteJson(new { ok = false, error = error.Message });
                return 1;
            }
        }

        private static void WaitForStats(Client client)
        {
            var received = false;
            var result = 0;
            var callback = client.CreateAndRegisterCallback<SAM.API.Callbacks.UserStatsReceived>();
            callback.OnRun += param =>
            {
                received = true;
                result = param.Result;
            };

            var steamId = client.SteamUser.GetSteamId();
            var handle = client.SteamUserStats.RequestUserStats(steamId);
            if (handle == CallHandle.Invalid)
            {
                throw new InvalidOperationException("Не удалось запросить статистику Steam.");
            }

            var deadline = DateTime.UtcNow.AddSeconds(12);
            while (!received && DateTime.UtcNow < deadline)
            {
                client.RunCallbacks(false);
                Thread.Sleep(50);
            }

            if (!received)
            {
                throw new TimeoutException("Steam не вернул статистику за 12 секунд.");
            }
            if (result != 1)
            {
                throw new InvalidOperationException($"Steam вернул ошибку статистики: {result}.");
            }
        }

        private static string GetSteamPath(string[] args)
        {
            var env = Environment.GetEnvironmentVariable("GAMEHELPER_STEAM_PATH");
            if (!string.IsNullOrWhiteSpace(env))
            {
                return env;
            }
            return args.Length >= 4 ? args[3] : null;
        }

        private static List<AchievementDto> LoadAchievements(Client client, long appId, string steamPath)
        {
            var definitions = SchemaReader.Load(appId, client.SteamApps008.GetCurrentGameLanguage(), steamPath);
            var achievements = new List<AchievementDto>();
            foreach (var def in definitions)
            {
                if (string.IsNullOrWhiteSpace(def.Id))
                {
                    continue;
                }
                if (!client.SteamUserStats.GetAchievementAndUnlockTime(def.Id, out var achieved, out var unlockTime))
                {
                    continue;
                }
                achievements.Add(new AchievementDto
                {
                    Id = def.Id,
                    Name = string.IsNullOrWhiteSpace(def.Name) ? def.Id : def.Name,
                    Description = def.Description ?? "",
                    IsHidden = def.IsHidden,
                    IsAchieved = achieved,
                    UnlockTime = achieved && unlockTime > 0 ? unlockTime : 0,
                    Icon = achieved || string.IsNullOrWhiteSpace(def.IconLocked) ? def.IconNormal : def.IconLocked,
                });
            }
            return achievements;
        }

        private static void WriteJson(object value)
        {
            Console.OutputEncoding = Encoding.UTF8;
            Console.WriteLine(Json.Write(value));
        }
    }

    internal static class Json
    {
        public static string Write(object value)
        {
            if (value == null)
            {
                return "null";
            }
            if (value is string text)
            {
                return Quote(text);
            }
            if (value is bool boolean)
            {
                return boolean ? "true" : "false";
            }
            if (value is int or long or uint or ulong)
            {
                return Convert.ToString(value, CultureInfo.InvariantCulture);
            }
            if (value is System.Collections.IEnumerable enumerable && value is not string)
            {
                return "[" + string.Join(",", enumerable.Cast<object>().Select(Write)) + "]";
            }

            var properties = value.GetType().GetProperties(BindingFlags.Instance | BindingFlags.Public);
            return "{" + string.Join(",", properties.Select(property =>
                Quote(ToCamelCase(property.Name)) + ":" + Write(property.GetValue(value)))) + "}";
        }

        private static string Quote(string text)
        {
            var builder = new StringBuilder();
            builder.Append('"');
            foreach (var c in text ?? "")
            {
                builder.Append(c switch
                {
                    '\\' => "\\\\",
                    '"' => "\\\"",
                    '\n' => "\\n",
                    '\r' => "\\r",
                    '\t' => "\\t",
                    _ => c < 32 ? $"\\u{(int)c:x4}" : c.ToString(),
                });
            }
            builder.Append('"');
            return builder.ToString();
        }

        private static string ToCamelCase(string value) =>
            string.IsNullOrEmpty(value) ? value : char.ToLowerInvariant(value[0]) + value.Substring(1);
    }

    internal sealed class AchievementDto
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public bool IsHidden { get; set; }
        public bool IsAchieved { get; set; }
        public uint UnlockTime { get; set; }
        public string Icon { get; set; }
    }

    internal sealed class AchievementDefinition
    {
        public string Id;
        public string Name;
        public string Description;
        public string IconNormal;
        public string IconLocked;
        public bool IsHidden;
    }

    internal static class SchemaReader
    {
        public static List<AchievementDefinition> Load(long appId, string language, string explicitSteamPath)
        {
            var steamPath = !string.IsNullOrWhiteSpace(explicitSteamPath) ? explicitSteamPath : Steam.GetInstallPath();
            var path = Path.Combine(steamPath, "appcache", "stats", $"UserGameStatsSchema_{appId}.bin");
            if (!File.Exists(path))
            {
                throw new FileNotFoundException($"Файл схемы достижений не найден: {path}", path);
            }
            var kv = KeyValue.LoadAsBinary(path);
            if (kv == null)
            {
                throw new InvalidDataException($"Не удалось прочитать схему достижений: {path}");
            }

            var stats = kv[appId.ToString(CultureInfo.InvariantCulture)]["stats"];
            if (!stats.Valid || stats.Children == null)
            {
                return new List<AchievementDefinition>();
            }

            var result = new List<AchievementDefinition>();
            foreach (var stat in stats.Children)
            {
                var type = stat["type"].AsString("");
                var typeInt = stat["type_int"].AsInteger(0);
                var isAchievements = type.Equals("ACHIEVEMENTS", StringComparison.OrdinalIgnoreCase) || typeInt == 4 || typeInt == 5;
                if (!isAchievements || stat.Children == null)
                {
                    continue;
                }

                foreach (var bits in stat.Children.Where(item => item.Name.Equals("bits", StringComparison.OrdinalIgnoreCase)))
                {
                    if (bits.Children == null)
                    {
                        continue;
                    }
                    foreach (var bit in bits.Children)
                    {
                        var id = bit["name"].AsString("");
                        result.Add(new AchievementDefinition
                        {
                            Id = id,
                            Name = GetLocalizedString(bit["display"]["name"], language, id),
                            Description = GetLocalizedString(bit["display"]["desc"], language, ""),
                            IconNormal = bit["display"]["icon"].AsString(""),
                            IconLocked = bit["display"]["icon_gray"].AsString(""),
                            IsHidden = bit["display"]["hidden"].AsBoolean(false),
                        });
                    }
                }
            }
            return result;
        }

        private static string GetLocalizedString(KeyValue value, string language, string fallback)
        {
            if (value.Valid == false)
            {
                return fallback;
            }
            if (value.Type == KeyValueType.String)
            {
                return value.AsString(fallback);
            }
            return value[language].AsString(value["english"].AsString(fallback));
        }
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace GameHelper.SamHelper
{
    internal class KeyValue
    {
        private static readonly KeyValue Invalid = new();
        public string Name = "<root>";
        public KeyValueType Type = KeyValueType.None;
        public object Value;
        public bool Valid;
        public List<KeyValue> Children;

        public KeyValue this[string key] => this.Children?.SingleOrDefault(
            child => child.Name.Equals(key, StringComparison.OrdinalIgnoreCase)) ?? Invalid;

        public string AsString(string defaultValue) => this.Valid && this.Value != null ? this.Value.ToString() : defaultValue;

        public int AsInteger(int defaultValue)
        {
            if (!this.Valid)
            {
                return defaultValue;
            }
            return this.Type switch
            {
                KeyValueType.String => int.TryParse((string)this.Value, out var value) ? value : defaultValue,
                KeyValueType.Int32 => (int)this.Value,
                KeyValueType.Float32 => (int)((float)this.Value),
                KeyValueType.UInt64 => (int)((ulong)this.Value & 0xFFFFFFFF),
                _ => defaultValue,
            };
        }

        public bool AsBoolean(bool defaultValue)
        {
            if (!this.Valid)
            {
                return defaultValue;
            }
            return this.Type switch
            {
                KeyValueType.String => int.TryParse((string)this.Value, out var value) ? value != 0 : defaultValue,
                KeyValueType.Int32 => (int)this.Value != 0,
                KeyValueType.Float32 => (int)((float)this.Value) != 0,
                KeyValueType.UInt64 => (ulong)this.Value != 0,
                _ => defaultValue,
            };
        }

        public static KeyValue LoadAsBinary(string path)
        {
            if (!File.Exists(path))
            {
                return null;
            }
            using var input = File.Open(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            var kv = new KeyValue();
            return kv.ReadAsBinary(input) ? kv : null;
        }

        public bool ReadAsBinary(Stream input)
        {
            this.Children = new List<KeyValue>();
            try
            {
                while (true)
                {
                    var type = (KeyValueType)input.ReadValueU8();
                    if (type == KeyValueType.End)
                    {
                        break;
                    }
                    var current = new KeyValue { Type = type, Name = input.ReadStringUnicode() };
                    switch (type)
                    {
                        case KeyValueType.None:
                            current.ReadAsBinary(input);
                            break;
                        case KeyValueType.String:
                            current.Valid = true;
                            current.Value = input.ReadStringUnicode();
                            break;
                        case KeyValueType.Int32:
                            current.Valid = true;
                            current.Value = input.ReadValueS32();
                            break;
                        case KeyValueType.UInt64:
                            current.Valid = true;
                            current.Value = input.ReadValueU64();
                            break;
                        case KeyValueType.Float32:
                            current.Valid = true;
                            current.Value = input.ReadValueF32();
                            break;
                        case KeyValueType.Color:
                        case KeyValueType.Pointer:
                            current.Valid = true;
                            current.Value = input.ReadValueU32();
                            break;
                        default:
                            throw new FormatException($"unsupported key value type {type} at {input.Position}");
                    }
                    this.Children.Add(current);
                }
                this.Valid = true;
                return true;
            }
            catch (Exception error)
            {
                Console.Error.WriteLine(error.ToString());
                return false;
            }
        }
    }
}

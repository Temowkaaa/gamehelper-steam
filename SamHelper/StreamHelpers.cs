using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text;

namespace GameHelper.SamHelper
{
    internal static class StreamHelpers
    {
        public static byte ReadValueU8(this Stream stream) => (byte)stream.ReadByte();

        public static int ReadValueS32(this Stream stream)
        {
            var data = new byte[4];
            Debug.Assert(stream.Read(data, 0, 4) == 4);
            return BitConverter.ToInt32(data, 0);
        }

        public static uint ReadValueU32(this Stream stream)
        {
            var data = new byte[4];
            Debug.Assert(stream.Read(data, 0, 4) == 4);
            return BitConverter.ToUInt32(data, 0);
        }

        public static ulong ReadValueU64(this Stream stream)
        {
            var data = new byte[8];
            Debug.Assert(stream.Read(data, 0, 8) == 8);
            return BitConverter.ToUInt64(data, 0);
        }

        public static float ReadValueF32(this Stream stream)
        {
            var data = new byte[4];
            Debug.Assert(stream.Read(data, 0, 4) == 4);
            return BitConverter.ToSingle(data, 0);
        }

        public static string ReadStringUnicode(this Stream stream)
        {
            var end = "\0";
            var i = 0;
            var data = new byte[128];
            while (true)
            {
                if (i + 1 > data.Length)
                {
                    Array.Resize(ref data, data.Length + 128);
                }
                Debug.Assert(stream.Read(data, i, 1) == 1);
                if (Encoding.UTF8.GetString(data, i, 1) == end)
                {
                    break;
                }
                i += 1;
            }
            return i == 0 ? "" : Encoding.UTF8.GetString(data, 0, i);
        }
    }
}

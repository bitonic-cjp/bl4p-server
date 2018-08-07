import struct

from . import bl4p_proto_pb2



id2type = \
{
bl4p_proto_pb2.Msg_BL4P_Start: bl4p_proto_pb2.BL4P_Start,
bl4p_proto_pb2.Msg_BL4P_StartResult: bl4p_proto_pb2.BL4P_StartResult,
}

type2id = {v:k for k,v in id2type.items()}



def serialize(obj):
	typeID = type2id[obj.__class__]
	typeID = struct.pack('<I', typeID) #32-bit little endian
	serialized = obj.SerializeToString()
	return typeID + serialized


def deserialize(message):
	typeID = struct.unpack('<I', message[:4])[0] #32-bit little endian
	serialized = message[4:]
	obj = id2type[typeID]()
	obj.ParseFromString(serialized)
	return obj


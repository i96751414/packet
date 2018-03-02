<h1 align="center">
  <img alt="packet" src="https://www.python.org/static/opengraph-icon-200x200.png" width="200px" height="200px"/>
  <br/>
  packet
</h1>
<p align="center">A simple object serializer which can be used in socket communications</p>
<div align="center">
  <a href="https://www.codacy.com/app/i96751414/packet?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=i96751414/packet&amp;utm_campaign=Badge_Grade"><img alt="Codacy Badge" src="https://api.codacy.com/project/badge/Grade/adbb128267164e688fd8244a061618fc" /></a>
</div>
<br/>

packet is a python package which allows to serialize objects in a safe way and send them over sockets. The main purpose of packet is to simplify the developer's work and, therefore, its usage is very simple.
Please keep in mind that packet is not thread-safe - make sure you don't modify the object tree while it is being serialized.

packet provides four main classes (```Packet```, ```SafePacket```, ```InspectedPacket``` and ```InspectedSafePacket```) with a set of common methods to be used (see [API](#api) section). It uses **json** (default) or **ast**/**repr** as the serializer/deserializer and further encryption may be added, so you can be assured it is completely safe.

## Which class to use?
    
Which class to use depends on your application's purpose. Below are specified all the classes which can be used:

- **Packet**

    The Packet class is the simplest one. Here, the dumped/loaded data is not encrypted/decrypted and the attributes are not inspected so, when loading data, the attributes will be updated as long as their name are the same. This is the reason why Packet only allows basic types.

- **SafePacket**

    Same as Packet class, however the dumped/loaded data is encrypted/decrypted using CBC (Cipher Block Chaining) or CTR (Counter Cipher) mode and a specified key.

- **InspectedPacket**

    With InspectedPacket the data to be loaded must match the current data, that is, if attribute "a" is of type int, only integers are allowed to be loaded on attribute "a". This is the reason why you should avoid using None - there is not a different value that can be loaded. Since it is inspected, types other than basic types are allowed.

- **InspectedSafePacket**

    Same as InspectedPacket class, however the dumped/loaded data is encrypted/decrypted using CBC (Cipher Block Chaining) or CTR (Counter Cipher) mode and a specified key.

## Usage

Dump and load a simple packet.

```python
from packet import Packet

class ExamplePacket(Packet):
    def __init__(self):
        self.integer = int()
        self.float = float()
        
packet1 = ExamplePacket()
packet2 = ExamplePacket()

# Modify packet1 - Since we are using Packet, we could change the data types
packet1.integer = 123
packet1.float = 1.23

# Send packet1 data to packet2
packet2.loads(packet1.dumps())

print("int: %d, float: %f" % (packet2.integer, packet2.float))
```

Output:
```
int: 123, float: 1.23
```

## <a name="api"></a>API

#### Methods

- **safe_eval**(node_or_string) - Safely evaluate an expression node or a string containing a Python expression. The string or node provided may only consist of the following Python literal structures: strings, bytes, numbers, tuples, lists, dicts, sets, booleans, and None. Note: This is a modified version of the ast.literal_eval function from Python 3.6
- **set_packet_serializer**(serializer) - Set serializer to be used in all packets. Serializer must be either ```JSON_SERIALIZER``` or ```AST_SERIALIZER```.
- **set_packet_encryption_key**(key) - Set encryption key to be used when serializing packets. Encryption key must be a string.
- **set_packet_encryption_mode**(mode) - Set encryption mode to be used when serializing packets. Encryption mode must be either ```CBC_MODE``` or ```CTR_MODE```.
- **set_ast_serializer**() - Set ```AST_SERIALIZER``` as the serializer to be used in all packets. Same as ```set_packet_serializer(AST_SERIALIZER)```.
- **set_json_serializer**() - Set ```JSON_SERIALIZER``` as the serializer to be used in all packets. Same as ```set_packet_serializer(JSON_SERIALIZER)```.
- **set_cbc_mode**() - Set ```CBC_MODE``` as the encryption mode to be used when serializing packets. Same as ```set_packet_encryption_mode(CBC_MODE)```.
- **set_ctr_mode**() - Set ```CTR_MODE``` as the encryption mode to be used when serializing packets. Same as ```set_packet_encryption_mode(CTR_MODE)```.

#### Classes

- **Packet**
- **SafePacket**
- **InspectedPacket**
- **InspectedSafePacket**

###### Common Methods

- .**dump**(fp)

    Serialize packet object to ```fp``` (a ```.write()``` supporting file-like object). Raises ```NotSerializable``` if the packet is not serializable.

- .**dumps**()
    
    Serialize packet object to string/bytes using the packet name as the tag - this can be then loaded using .**load**() method, as specified below. Raises ```NotSerializable``` if the packet is not serializable.

- .**load**(fp)

    Deserialize data from ```fp``` (a ```.read()``` supporting file-like object) and update packet object. Raises ```UnknownPacket``` or ```InvalidData``` if the data is not deserializable.

- .**loads**(data)

    Deserialize ```data``` and update packet object. Raises ```UnknownPacket``` or ```InvalidData``` if the data is not deserializable.

- .**receive_from**(conn, buffer_size=512)

    Receive data from a connection ```conn``` (typically a socket connection) by doing ```conn.recv(buffer_size)``` and loads the received data into the packet. If there is an error loading data or no data is obtained, returns ```False```, otherwise returns ```True```.

- .**send_to**(conn)

    Send data to a connection ```conn``` (typically a socket connection). If no connection, returns ```None```, otherwise returns the same as ```conn.send(data)```.

#### Constants

- **JSON_SERIALIZER**
- **AST_SERIALIZER**
- **CBC_MODE**
- **CTR_MODE**

#### Exceptions
    
- **UnknownPacket**
- **InvalidData**
- **UnknownEncryption**
- **NotSerializable**

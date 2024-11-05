import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/services.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:permission_handler/permission_handler.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Acc value sender by WebSocket',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const MyHomePage(title: 'Specify the server IP address'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  WebSocketChannel? channel;
  String isConnectedString = 'Not connected';
  String serverIP = '';
  String portNumber = '';
  @override
  void initState() {
    super.initState();
    userAccelerometerEventStream(samplingPeriod: SensorInterval.fastestInterval)
        .listen((UserAccelerometerEvent event) {
      if (channel != null) {
        channel?.sink.add('g, ${event.x}, ${event.y}, ${event.z}');
        isConnectedString = 'Connected';
      } else {
        if (isConnectedString != "Failed to connect") {
          isConnectedString = 'Not connected';
        }
      }
    });
    gyroscopeEventStream(samplingPeriod: SensorInterval.fastestInterval)
        .listen((GyroscopeEvent event) {
      channel?.sink.add('r, ${event.x}, ${event.y}, ${event.z}');
    });
  }

  Future<bool> _requestPermissions() async {
    return await Permission.sensors.request().isGranted;
  }

  void _connect() {
    try {
      channel = WebSocketChannel.connect(
        Uri.parse('ws://$serverIP:$portNumber'),
      );
    } catch (e) {
      isConnectedString = 'Failed to connect';
      return;
    }
    isConnectedString = 'Connected';
    return;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            TextField(
              autofocus: true,
              controller: TextEditingController(),
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'Server IP address',
              ),
              onChanged: (text) => serverIP = text,
            ),
            TextField(
              controller: TextEditingController(),
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'Port number',
              ),
              inputFormatters: [
                LengthLimitingTextInputFormatter(5),
                FilteringTextInputFormatter.digitsOnly
              ],
              onChanged: (value) => portNumber = value,
            ),
            Text(
              'Connection status: $isConnectedString',
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _connect,
        tooltip: 'Start sending',
        child: const Icon(Icons.sensors),
      ), // This trailing comma makes auto-formatting nicer for build methods.
    );
  }
}

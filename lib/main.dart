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
    _requestPermissions().then((granted) {
      if (granted) {
        // 重力加速度を含む加速度
        accelerometerEventStream(samplingPeriod: SensorInterval.fastestInterval)
            .listen((event) {
          if (channel != null) {
            channel?.sink.add('a, ${event.x}, ${event.y}, ${event.z}');
            isConnectedString = 'Connected';
          } else {
            isConnectedString = 'Not connected';
          }
        });

        // 重力加速度を除いた純粋な加速度
        userAccelerometerEventStream(
                samplingPeriod: SensorInterval.fastestInterval)
            .listen((event) {
          channel?.sink.add('g, ${event.x}, ${event.y}, ${event.z}');
        });

        // ジャイロスコープ
        gyroscopeEventStream(samplingPeriod: SensorInterval.fastestInterval)
            .listen((GyroscopeEvent event) {
          channel?.sink.add('r, ${event.x}, ${event.y}, ${event.z}');
        });
      }
    });
  }

  Future<bool> _requestPermissions() async {
    var status = await Permission.sensors.status;
    if (status.isDenied) {
      status = await Permission.sensors.request();
    }
    return status.isGranted;
  }

  void _connect() {
    try {
      channel = WebSocketChannel.connect(
        Uri.parse('ws://$serverIP:$portNumber/data'),
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
            Container(
              width: 280, // スマホ画面に適したサイズ
              margin: const EdgeInsets.symmetric(vertical: 8), // 上下の余白
              child: TextField(
                autofocus: true,
                controller: TextEditingController(),
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: 'Server IP address',
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
                onChanged: (text) => serverIP = text,
              ),
            ),
            Container(
              width: 280, // スマホ画面に適したサイズ
              margin: const EdgeInsets.symmetric(vertical: 8), // 上下の余白
              child: TextField(
                controller: TextEditingController(),
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: 'Port number',
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
                inputFormatters: [
                  LengthLimitingTextInputFormatter(5),
                  FilteringTextInputFormatter.digitsOnly
                ],
                onChanged: (value) => portNumber = value,
              ),
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

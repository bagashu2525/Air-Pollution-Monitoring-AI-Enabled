import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'dart:async';
import 'login_page.dart';
import 'risk_tab.dart';
import 'admin_dashboard.dart';

void main() {
  runApp(PollutionApp());
}

class PollutionApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Pollution Monitoring System',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        brightness: Brightness.light,
      ),
      darkTheme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        brightness: Brightness.dark,
      ),
      themeMode: ThemeMode.system,
      home: AuthWrapper(),
    );
  }
}

class AuthWrapper extends StatefulWidget {
  @override
  _AuthWrapperState createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  bool _isLoggedIn = false;
  bool _isAdminMode = true; // Default to admin mode when logged in

  void _handleLogin(bool success) {
    setState(() {
      _isLoggedIn = success;
    });
  }

  void _handleLogout() {
    setState(() {
      _isLoggedIn = false;
    });
  }

  void _toggleMode() {
    setState(() {
      _isAdminMode = !_isAdminMode;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoggedIn) {
      if (_isAdminMode) {
        return AdminDashboard(
          onLogout: _handleLogout,
          onSwitchToUserMode: _toggleMode,
        );
      } else {
        return PollutionHomePage(
          onLogout: _handleLogout,
          onSwitchToAdminMode: _toggleMode,
        );
      }
    } else {
      return LoginPage(onLogin: _handleLogin);
    }
  }
}

class PollutionHomePage extends StatefulWidget {
  final Function onLogout;
  final Function onSwitchToAdminMode;

  const PollutionHomePage({
    Key? key, 
    required this.onLogout,
    required this.onSwitchToAdminMode,
  }) : super(key: key);

  @override
  _PollutionHomePageState createState() => _PollutionHomePageState();
}

class _PollutionHomePageState extends State<PollutionHomePage> with SingleTickerProviderStateMixin {
  Map<String, dynamic> _sensorData = {};
  bool _loading = true;
  String? _error;
  late TabController _tabController;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _fetchSensorData();
    _refreshTimer = Timer.periodic(Duration(seconds: 15), (timer) => _fetchSensorData());
  }

  @override
  void dispose() {
    _tabController.dispose();
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchSensorData() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final response = await http.get(Uri.parse('http://192.168.193.53:5000/api/sensor-data'));
      if (response.statusCode == 200) {
        
        setState(() {
          _sensorData = jsonDecode(response.body);
          print('Fetched pollutant data: ${_sensorData['pollutants']}');
          _loading = false;
        });
      } else {
        setState(() {
          _error = 'Failed to fetch data: ${response.statusCode}';
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Pollution Monitoring System'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(icon: Icon(Icons.cloud), text: 'Pollutants'),
            Tab(icon: Icon(Icons.warning), text: 'Risks'),
            Tab(icon: Icon(Icons.analytics), text: 'Analytics'),
          ],
        ),
        actions: [
          IconButton(icon: Icon(Icons.refresh), onPressed: _fetchSensorData),
          IconButton(
            icon: Icon(Icons.admin_panel_settings),
            onPressed: () => widget.onSwitchToAdminMode(),
            tooltip: 'Switch to Admin Mode',
          ),
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: () => widget.onLogout(),
            tooltip: 'Logout',
          ),
        ],
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: TextStyle(color: Colors.red)))
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildPollutantsTab(),
                    RiskTab(sensorData: _sensorData),
                    _buildAnalyticsTab(),
                  ],
                ),
    );
  }

    Widget _buildPollutantsTab() {
  final pollutants = _sensorData['pollutants'] as Map<String, dynamic>? ?? {};
  final explosionParameters = _sensorData['explosion_parameters'] as Map<String, dynamic>? ?? {};

  return SingleChildScrollView(
    padding: const EdgeInsets.all(16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Pollutants Section
        Text('Pollutants', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),

        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: pollutants.entries.map((entry) {
            final value = entry.value;
            final doubleValue = value is num ? value.toDouble() : 0.0;
            return SizedBox(
              width: MediaQuery.of(context).size.width / 2 - 26, // for spacing and padding
              child: _buildParameterCard(
                entry.key,
                doubleValue.toStringAsFixed(3),
                'mg/m³',
                _getTrendIcon(doubleValue),
              ),
            );
          }).toList(),
        ),

        const SizedBox(height: 24),

        // Explosion Parameters Section
        Text('Explosion Parameters', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),

        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: explosionParameters.entries.map((entry) {
            final value = entry.value;
            final doubleValue = value is num ? value.toDouble() : 0.0;
            return SizedBox(
              width: MediaQuery.of(context).size.width / 2 - 26,
              child: _buildParameterCard(
                entry.key,
                doubleValue.toStringAsFixed(2),
                _getUnit(entry.key),
                _getTrendIcon(doubleValue),
              ),
            );
          }).toList(),
        ),
      ],
    ),
  );
}


  Widget _buildParameterCard(String title, String value, String unit, IconData trendIcon) {
    return Card(
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(10), // Reduced padding
        child: Column(
          mainAxisSize: MainAxisSize.min, // Use minimum space needed
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.bold),
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
            ),
            const SizedBox(height: 6), // Reduced spacing
            Row(
              children: [
                Expanded(
                  child: Text(
                    value,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), // Reduced font size
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 4),
                Icon(trendIcon, size: 16, color: _getTrendColor(trendIcon)),
              ],
            ),
            Text(unit, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
          ],
        ),
      ),
    );
  }

  String _getUnit(String parameter) {
    final units = {
      'Methane': 'ppm',
      'Hydrogen': 'ppm',
      'Temperature': '°C',
      'Pressure': 'bar',
      'Oxygen_Level': '%',
      'VOC': 'ppm',
    };
    return units[parameter] ?? '';
  }

  IconData _getTrendIcon(dynamic value) {
    // This is a placeholder for trend analysis
    // In a real app, you would compare with previous values
    final random = value.hashCode % 3;
    if (random == 0) {
      return Icons.arrow_upward;
    } else if (random == 1) {
      return Icons.arrow_downward;
    } else {
      return Icons.remove;
    }
  }

  Color _getTrendColor(IconData icon) {
    if (icon == Icons.arrow_upward) {
      return Colors.red;
    } else if (icon == Icons.arrow_downward) {
      return Colors.green;
    } else {
      return Colors.grey;
    }
  }

  Widget _buildAnalyticsTab() {
  final pollutants = _sensorData['pollutants'] as Map<String, dynamic>? ?? {};

  final data = pollutants.entries.mapIndexed((i, entry) {
    return BarChartRodData(
      toY: double.tryParse(entry.value.toString()) ?? 0.0,
      color: Colors.blue,
    );
  }).toList();

  final maxY = data.map((e) => e.toY).fold<double>(0.0, (prev, curr) => curr > prev ? curr : prev);

  return Padding(
    padding: const EdgeInsets.all(16.0),
    child: BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: maxY * 1.2, // 20% padding
        barGroups: data
            .asMap()
            .map((index, rodData) => MapEntry(
                  index,
                  BarChartGroupData(x: index, barRods: [rodData]),
                ))
            .values
            .toList(),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                final keyList = pollutants.keys.toList();
                if (value.toInt() < keyList.length) {
                  return Text(
                    keyList[value.toInt()],
                    style: TextStyle(fontSize: 10),
                  );
                }
                return Text('');
              },
            ),
          ),
        ),
      ),
    ),
  );
}


  Widget _buildInfoCard(String title, String value, IconData icon, Color color) {
    return Card(
      elevation: 3,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(icon, color: color, size: 40),
            SizedBox(width: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontSize: 14, color: Colors.grey)),
                SizedBox(height: 4),
                Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

extension MapEntryIndexed<K, V> on Iterable<MapEntry<K, V>> {
  Iterable<T> mapIndexed<T>(T Function(int index, MapEntry<K, V> entry) f) {
    int index = 0;
    return this.map((entry) => f(index++, entry));
  }
}

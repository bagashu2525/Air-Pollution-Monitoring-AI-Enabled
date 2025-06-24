import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class AdminDashboard extends StatefulWidget {
  final Function onLogout;
  final Function onSwitchToUserMode;

  const AdminDashboard({
    Key? key, 
    required this.onLogout,
    required this.onSwitchToUserMode,
  }) : super(key: key);

  @override
  _AdminDashboardState createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic> _thresholds = {};
  List<Map<String, dynamic>> _actions = [];
  bool _isLoading = false;
  String? _error;

  // Controllers for adding new action
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  String _selectedPriority = 'MEDIUM';

  // Controllers for thresholds
  final Map<String, TextEditingController> _thresholdControllers = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _titleController.dispose();
    _descriptionController.dispose();
    _thresholdControllers.values.forEach((controller) => controller.dispose());
    super.dispose();
  }

  Future<void> _fetchData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await http.get(Uri.parse('http://192.168.193.53:5000/api/admin/settings'));
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _thresholds = data['thresholds'] ?? {};
          _actions = List<Map<String, dynamic>>.from(data['recommended_actions'] ?? []);
          
          // Initialize controllers for thresholds
          _thresholds.forEach((key, value) {
            _thresholdControllers[key] = TextEditingController(text: value.toString());
          });
          
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Failed to fetch data: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _saveThresholds() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Convert controllers to values
      // Add explicit type declaration here
      final Map<String, dynamic> updatedThresholds = {};
      _thresholdControllers.forEach((key, controller) {
        updatedThresholds[key] = double.tryParse(controller.text) ?? 0.0;
      });

      final response = await http.post(
        Uri.parse('http://192.168.193.53:5000/api/admin/thresholds'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(updatedThresholds),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Thresholds updated successfully')),
        );
        setState(() {
          _thresholds = updatedThresholds;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Failed to update thresholds: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _saveAction(Map<String, dynamic> action, [int? index]) async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await http.post(
        Uri.parse('http://192.168.193.53:5000/api/admin/actions'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'action': action,
          'index': index,
        }),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(index != null ? 'Action updated' : 'Action added')),
        );
        _fetchData(); // Refresh data
      } else {
        setState(() {
          _error = 'Failed to save action: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _deleteAction(int index) async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await http.delete(
        Uri.parse('http://192.168.193.53:5000/api/admin/actions/$index'),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Action deleted')),
        );
        setState(() {
          _actions.removeAt(index);
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Failed to delete action: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  void _showAddActionDialog([Map<String, dynamic>? existingAction, int? index]) {
    if (existingAction != null) {
      _titleController.text = existingAction['title'] ?? '';
      _descriptionController.text = existingAction['description'] ?? '';
      _selectedPriority = existingAction['priority'] ?? 'MEDIUM';
    } else {
      _titleController.clear();
      _descriptionController.clear();
      _selectedPriority = 'MEDIUM';
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(existingAction != null ? 'Edit Action' : 'Add New Action'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _titleController,
                decoration: InputDecoration(labelText: 'Title'),
              ),
              SizedBox(height: 16),
              TextField(
                controller: _descriptionController,
                decoration: InputDecoration(labelText: 'Description'),
                maxLines: 3,
              ),
              SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _selectedPriority,
                decoration: InputDecoration(labelText: 'Priority'),
                items: ['LOW', 'MEDIUM', 'HIGH'].map((priority) {
                  return DropdownMenuItem(
                    value: priority,
                    child: Text(priority),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() {
                    _selectedPriority = value!;
                  });
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              if (_titleController.text.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Title cannot be empty')),
                );
                return;
              }
              
              final action = {
                'title': _titleController.text,
                'description': _descriptionController.text,
                'priority': _selectedPriority,
              };
              
              Navigator.pop(context);
              _saveAction(action, index);
            },
            child: Text('Save'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // In the build method of _AdminDashboardState
      appBar: AppBar(
        title: Text('Admin Dashboard'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(icon: Icon(Icons.warning), text: 'Thresholds'),
            Tab(icon: Icon(Icons.assignment), text: 'Actions'),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _fetchData,
            tooltip: 'Refresh',
          ),
          IconButton(
            icon: Icon(Icons.visibility),
            onPressed: () => widget.onSwitchToUserMode(),
            tooltip: 'Switch to User Mode',
          ),
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: () => widget.onLogout(),
            tooltip: 'Logout',
          ),
        ],
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: TextStyle(color: Colors.red)))
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildThresholdsTab(),
                    _buildActionsTab(),
                  ],
                ),
    );
  }

  Widget _buildThresholdsTab() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Alert Thresholds',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: _thresholdControllers.length,
              itemBuilder: (context, index) {
                final entry = _thresholdControllers.entries.elementAt(index);
                return Card(
                  margin: EdgeInsets.only(bottom: 8),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: Text(
                            entry.key,
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                        ),
                        Expanded(
                          flex: 3,
                          child: TextField(
                            controller: entry.value,
                            decoration: InputDecoration(
                              labelText: 'Threshold',
                              border: OutlineInputBorder(),
                            ),
                            keyboardType: TextInputType.number,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          SizedBox(height: 16),
          ElevatedButton(
            onPressed: _saveThresholds,
            child: Text('Save Thresholds'),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionsTab() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Recommended Actions',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              ElevatedButton.icon(
                onPressed: () => _showAddActionDialog(),
                icon: Icon(Icons.add),
                label: Text('Add'),
              ),
            ],
          ),
          SizedBox(height: 16),
          Expanded(
            child: ListView.builder(
              itemCount: _actions.length,
              itemBuilder: (context, index) {
                final action = _actions[index];
                return Card(
                  margin: EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text(action['title'] ?? ''),
                    subtitle: Text(action['description'] ?? ''),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _getPriorityColor(action['priority']),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            action['priority'] ?? 'MEDIUM',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ),
                        IconButton(
                          icon: Icon(Icons.edit),
                          onPressed: () => _showAddActionDialog(action, index),
                        ),
                        IconButton(
                          icon: Icon(Icons.delete),
                          onPressed: () => _deleteAction(index),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Color _getPriorityColor(String? priority) {
    switch (priority?.toUpperCase()) {
      case 'LOW':
        return Colors.blue;
      case 'MEDIUM':
        return Colors.orange;
      case 'HIGH':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}
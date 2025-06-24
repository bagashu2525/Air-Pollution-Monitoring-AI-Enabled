import 'package:flutter/material.dart';

class RiskTab extends StatelessWidget {
  final Map<String, dynamic> sensorData;

  const RiskTab({Key? key, required this.sensorData}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final explosionRisks = sensorData['explosion_risks'] as List<dynamic>? ?? [];
    final alerts = sensorData['alerts'] as List<dynamic>? ?? [];
    final rawRisk = sensorData['risk_level'];
    final riskLevel = _parseRiskLevel(rawRisk);
    final riskStatus = sensorData['risk_status']?.toString().toUpperCase() ?? 'UNKNOWN';
    final actions = sensorData['recommended_actions'] as List<dynamic>? ?? [];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildRiskLevelIndicator(context, riskLevel, riskStatus),
          const SizedBox(height: 24),

          if (explosionRisks.isNotEmpty) ...[
            Text('Explosion Risks', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            ...explosionRisks.map((risk) => _buildRiskCard(
                  context,
                  risk['type'] ?? 'Unknown Risk',
                  risk['description'] ?? 'No description available',
                  risk['severity'] ?? 'UNKNOWN',
                )),
            const SizedBox(height: 24),
          ],

          if (alerts.isNotEmpty) ...[
            Text('Alerts', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            ...alerts.map((alert) => _buildAlertCard(
                  context,
                  alert['parameter'] ?? 'Unknown',
                  alert['value']?.toString() ?? 'N/A',
                  alert['threshold']?.toString() ?? 'N/A',
                )),
            const SizedBox(height: 24),
          ],

          if (actions.isNotEmpty) ...[
            Text('Recommended Actions', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            ...actions.asMap().entries.map((entry) {
              final index = entry.key;
              final action = entry.value.toString();
              final priority = index < 2 ? 'HIGH' : index < 4 ? 'MEDIUM' : 'LOW';
              return _buildActionCard(context, 'Action ${index + 1}', action, priority);
            }),
          ],
        ],
      ),
    );
  }

  double _parseRiskLevel(dynamic rawRisk) {
    if (rawRisk is num) return rawRisk.toDouble();
    return double.tryParse(rawRisk?.toString() ?? '') ?? 0.0;
  }

  Widget _buildRiskLevelIndicator(BuildContext context, double riskLevel, String status) {
    final clampedValue = (riskLevel / 100).clamp(0.0, 1.0);
    final statusColor = _getColorForStatus(status);

    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Current Risk Level', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: LinearProgressIndicator(
                    value: clampedValue,
                    minHeight: 10,
                    backgroundColor: Colors.grey[300],
                    valueColor: AlwaysStoppedAnimation<Color>(statusColor),
                  ),
                ),
                const SizedBox(width: 16),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: statusColor,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    status,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Risk Level: ${riskLevel.toStringAsFixed(1)}%',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getColorForStatus(String status) {
    switch (status) {
      case 'LOW':
        return Colors.green;
      case 'MODERATE':
        return Colors.orange;
      case 'HIGH':
        return Colors.red;
      case 'CRITICAL':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  Widget _buildRiskCard(BuildContext context, String type, String description, String severity) {
    final severityColor = _getColorForSeverity(severity);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(type),
        subtitle: Text(description),
        leading: Icon(Icons.warning, color: severityColor),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: severityColor,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            severity.toUpperCase(),
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
          ),
        ),
      ),
    );
  }

  Color _getColorForSeverity(String severity) {
    switch (severity.toUpperCase()) {
      case 'LOW':
        return Colors.green;
      case 'MEDIUM':
        return Colors.orange;
      case 'HIGH':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  Widget _buildAlertCard(BuildContext context, String parameter, String value, String threshold) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(parameter),
        subtitle: Text('Current: $value | Threshold: $threshold'),
        leading: const Icon(Icons.notifications_active, color: Colors.red),
      ),
    );
  }

  Widget _buildActionCard(BuildContext context, String title, String description, String priority) {
    final priorityColor = _getColorForSeverity(priority); // Reusing same severity colors

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(title),
        subtitle: Text(description),
        leading: Icon(Icons.assignment, color: priorityColor),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: priorityColor,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            priority.toUpperCase(),
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
          ),
        ),
      ),
    );
  }
}

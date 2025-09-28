#!/usr/bin/env python3
"""
Performance monitoring script for Census ML API

This script continuously monitors the API performance and generates reports.

Usage:
    python scripts/performance_monitor.py --url http://localhost:8000 --interval 60
"""

import argparse
import time
import json
import logging
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import threading
from pathlib import Path


class APIMonitor:
    """API Performance Monitor"""
    
    def __init__(self, base_url: str, interval: int = 60):
        self.base_url = base_url.rstrip('/')
        self.interval = interval
        self.metrics_history: List[Dict[str, Any]] = []
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure logs directory exists
        Path('logs').mkdir(exist_ok=True)
    
    def check_health(self) -> Dict[str, Any]:
        """Check API health and collect metrics"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/v1/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'model_loaded': data.get('model_loaded', False),
                    'uptime_seconds': data.get('uptime_seconds', 0)
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'error': f'HTTP {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'response_time': None
            }
    
    def check_prediction_performance(self) -> Dict[str, Any]:
        """Test prediction endpoint performance"""
        test_data = {
            "age": 37,
            "workclass": "Private",
            "fnlgt": 178356,
            "education": "HS-grad",
            "education-num": 10,
            "marital-status": "Married-civ-spouse",
            "occupation": "Prof-specialty",
            "relationship": "Husband",
            "race": "White",
            "sex": "Male",
            "capital-gain": 0,
            "capital-loss": 0,
            "hours-per-week": 40,
            "native-country": "United-States"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/v1/predict",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'response_time': response_time,
                    'prediction': data.get('prediction'),
                    'confidence': data.get('confidence')
                }
            else:
                return {
                    'status': 'error',
                    'response_time': response_time,
                    'error': f'HTTP {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'response_time': None
            }
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """Get API metrics"""
        try:
            response = requests.get(f"{self.base_url}/v1/metrics", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}'}
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def run_load_test(self, num_requests: int = 10) -> Dict[str, Any]:
        """Run a mini load test"""
        results = []
        successful_requests = 0
        
        def make_request():
            nonlocal successful_requests
            result = self.check_prediction_performance()
            results.append(result)
            if result['status'] == 'success':
                successful_requests += 1
        
        # Create threads for concurrent requests
        threads = []
        start_time = time.time()
        
        for _ in range(num_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        response_times = [r['response_time'] for r in results if r.get('response_time') is not None]
        
        return {
            'total_requests': num_requests,
            'successful_requests': successful_requests,
            'success_rate': successful_requests / num_requests,
            'total_time': total_time,
            'avg_response_time': statistics.mean(response_times) if response_times else None,
            'min_response_time': min(response_times) if response_times else None,
            'max_response_time': max(response_times) if response_times else None,
            'median_response_time': statistics.median(response_times) if response_times else None
        }
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive metrics"""
        timestamp = datetime.utcnow().isoformat()
        
        self.logger.info("Collecting metrics...")
        
        # Basic health check
        health = self.check_health()
        
        # Prediction performance
        prediction = self.check_prediction_performance()
        
        # API metrics
        api_metrics = self.get_api_metrics()
        
        # Load test
        load_test = self.run_load_test(5)
        
        metrics = {
            'timestamp': timestamp,
            'health': health,
            'prediction': prediction,
            'api_metrics': api_metrics,
            'load_test': load_test
        }
        
        self.metrics_history.append(metrics)
        
        # Keep only last 100 metrics
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        return metrics
    
    def save_metrics(self, filename: Optional[str] = None):
        """Save metrics to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/metrics_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.metrics_history, f, indent=2, default=str)
        
        self.logger.info(f"Metrics saved to {filename}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        if not self.metrics_history:
            return {'error': 'No metrics available'}
        
        # Analyze recent metrics (last 10 entries)
        recent_metrics = self.metrics_history[-10:]
        
        # Health status
        health_statuses = [m['health']['status'] for m in recent_metrics]
        healthy_count = sum(1 for status in health_statuses if status == 'healthy')
        
        # Response times
        health_response_times = [
            m['health']['response_time'] for m in recent_metrics 
            if m['health'].get('response_time') is not None
        ]
        
        prediction_response_times = [
            m['prediction']['response_time'] for m in recent_metrics 
            if m['prediction'].get('response_time') is not None
        ]
        
        # Load test success rates
        success_rates = [
            m['load_test']['success_rate'] for m in recent_metrics 
            if 'load_test' in m and 'success_rate' in m['load_test']
        ]
        
        report = {
            'period': f"Last {len(recent_metrics)} checks",
            'health': {
                'availability': healthy_count / len(recent_metrics),
                'avg_response_time': statistics.mean(health_response_times) if health_response_times else None
            },
            'prediction': {
                'avg_response_time': statistics.mean(prediction_response_times) if prediction_response_times else None,
                'max_response_time': max(prediction_response_times) if prediction_response_times else None
            },
            'load_test': {
                'avg_success_rate': statistics.mean(success_rates) if success_rates else None,
                'min_success_rate': min(success_rates) if success_rates else None
            },
            'latest_metrics': recent_metrics[-1] if recent_metrics else None
        }
        
        return report
    
    def print_report(self):
        """Print formatted performance report"""
        report = self.generate_report()
        
        if 'error' in report:
            print(f"Error: {report['error']}")
            return
        
        print("\n" + "="*60)
        print(f"API PERFORMANCE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        print(f"\nPeriod: {report['period']}")
        
        print(f"\nHEALTH:")
        print(f"  Availability: {report['health']['availability']:.1%}")
        if report['health']['avg_response_time']:
            print(f"  Avg Response Time: {report['health']['avg_response_time']:.3f}s")
        
        print(f"\nPREDICTION PERFORMANCE:")
        if report['prediction']['avg_response_time']:
            print(f"  Avg Response Time: {report['prediction']['avg_response_time']:.3f}s")
        if report['prediction']['max_response_time']:
            print(f"  Max Response Time: {report['prediction']['max_response_time']:.3f}s")
        
        print(f"\nLOAD TEST:")
        if report['load_test']['avg_success_rate']:
            print(f"  Avg Success Rate: {report['load_test']['avg_success_rate']:.1%}")
        if report['load_test']['min_success_rate']:
            print(f"  Min Success Rate: {report['load_test']['min_success_rate']:.1%}")
        
        # Status indicators
        latest = report.get('latest_metrics', {})
        if latest:
            print(f"\nCURRENT STATUS:")
            print(f"  Health: {latest.get('health', {}).get('status', 'unknown').upper()}")
            if 'api_metrics' in latest and 'request_count' in latest['api_metrics']:
                print(f"  Total Requests: {latest['api_metrics']['request_count']}")
            if 'api_metrics' in latest and 'uptime_seconds' in latest['api_metrics']:
                uptime_hours = latest['api_metrics']['uptime_seconds'] / 3600
                print(f"  Uptime: {uptime_hours:.1f} hours")
        
        print("\n" + "="*60)
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.running = True
        self.logger.info(f"Starting API monitoring (interval: {self.interval}s)")
        
        try:
            while self.running:
                metrics = self.collect_metrics()
                
                # Print brief status
                health_status = metrics['health']['status']
                pred_status = metrics['prediction']['status']
                success_rate = metrics['load_test']['success_rate']
                
                self.logger.info(
                    f"Health: {health_status} | "
                    f"Prediction: {pred_status} | "
                    f"Load test success: {success_rate:.1%}"
                )
                
                # Check for alerts
                self.check_alerts(metrics)
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        finally:
            self.running = False
            self.save_metrics()
    
    def check_alerts(self, metrics: Dict[str, Any]):
        """Check for performance alerts"""
        alerts = []
        
        # Health check alerts
        if metrics['health']['status'] != 'healthy':
            alerts.append(f"API Health: {metrics['health']['status']}")
        
        # Response time alerts
        if metrics['health'].get('response_time', 0) > 5.0:
            alerts.append(f"Slow health response: {metrics['health']['response_time']:.2f}s")
        
        if metrics['prediction'].get('response_time', 0) > 2.0:
            alerts.append(f"Slow prediction response: {metrics['prediction']['response_time']:.2f}s")
        
        # Load test alerts
        if metrics['load_test']['success_rate'] < 0.8:
            alerts.append(f"Low success rate: {metrics['load_test']['success_rate']:.1%}")
        
        # Log alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='API Performance Monitor')
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--report', action='store_true', help='Generate single report and exit')
    parser.add_argument('--save', help='Save metrics to specific file')
    
    args = parser.parse_args()
    
    monitor = APIMonitor(args.url, args.interval)
    
    if args.report:
        # Single report mode
        monitor.collect_metrics()
        monitor.print_report()
        if args.save:
            monitor.save_metrics(args.save)
    else:
        # Continuous monitoring mode
        try:
            monitor.start_monitoring()
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            monitor.stop_monitoring()


if __name__ == '__main__':
    main()

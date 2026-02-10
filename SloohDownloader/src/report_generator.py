# -*- coding: utf-8 -*-
"""
Slooh Image Downloader - Report Generator
Generate reports in CSV and HTML formats
"""

import os
import csv
from datetime import datetime


class ReportGenerator(object):
    """Generate download reports in various formats"""
    
    def __init__(self, tracker, logger=None):
        """
        Initialize report generator.
        
        Args:
            tracker: DownloadTracker instance
            logger: Logger instance
        """
        self.tracker = tracker
        self.logger = logger
    
    def _log(self, level, message):
        """Internal logging helper"""
        if self.logger:
            if level == 'debug':
                self.logger.debug(message)
            elif level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
    
    def export_csv(self, output_path, filter_type=None, filter_object=None, 
                   filter_telescope=None):
        """
        Export download history to CSV file.
        
        Args:
            output_path: Path for output CSV file
            filter_type: Filter by image type (optional)
            filter_object: Filter by object name (optional)
            filter_telescope: Filter by telescope name (optional)
            
        Returns:
            bool: True if successful
        """
        try:
            images = self.tracker.get_downloaded_images(
                filter_type=filter_type,
                filter_object=filter_object,
                filter_telescope=filter_telescope
            )
            
            if not images:
                self._log('warning', "No images to export")
                return False
            
            # Write CSV
            with open(output_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'image_id', 'customer_image_id', 'mission_id', 'filename',
                    'object_name', 'telescope_name', 'image_type', 
                    'file_size', 'download_date', 'file_path'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for img in images:
                    row = {
                        'image_id': img.get('image_id', ''),
                        'customer_image_id': img.get('customer_image_id', ''),
                        'mission_id': img.get('mission_id', ''),
                        'filename': img.get('filename', ''),
                        'object_name': img.get('object_name', ''),
                        'telescope_name': img.get('telescope_name', ''),
                        'image_type': img.get('image_type', ''),
                        'file_size': img.get('file_size', 0),
                        'download_date': img.get('download_date', ''),
                        'file_path': img.get('file_path', '')
                    }
                    writer.writerow(row)
            
            self._log('info', "CSV report exported: {0} ({1} images)".format(
                output_path, len(images)))
            return True
            
        except Exception as e:
            self._log('error', "CSV export failed: {0}".format(str(e)))
            return False
    
    def export_html(self, output_path, filter_type=None, filter_object=None,
                    filter_telescope=None):
        """
        Export download history to HTML report.
        
        Args:
            output_path: Path for output HTML file
            filter_type: Filter by image type (optional)
            filter_object: Filter by object name (optional)
            filter_telescope: Filter by telescope name (optional)
            
        Returns:
            bool: True if successful
        """
        try:
            images = self.tracker.get_downloaded_images(
                filter_type=filter_type,
                filter_object=filter_object,
                filter_telescope=filter_telescope
            )
            
            stats = self.tracker.get_statistics()
            
            # Generate HTML
            html = self._generate_html(images, stats, filter_type, 
                                      filter_object, filter_telescope)
            
            with open(output_path, 'w') as f:
                f.write(html)
            
            self._log('info', "HTML report exported: {0}".format(output_path))
            return True
            
        except Exception as e:
            self._log('error', "HTML export failed: {0}".format(str(e)))
            return False
    
    def _generate_html(self, images, stats, filter_type, filter_object, filter_telescope):
        """Generate HTML report content"""
        
        # Build filter description
        filters_applied = []
        if filter_type:
            filters_applied.append("Type: {0}".format(filter_type))
        if filter_object:
            filters_applied.append("Object: {0}".format(filter_object))
        if filter_telescope:
            filters_applied.append("Telescope: {0}".format(filter_telescope))
        
        filter_text = ", ".join(filters_applied) if filters_applied else "None"
        
        # Format file size
        def format_size(bytes_size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return "{0:.2f} {1}".format(bytes_size, unit)
                bytes_size /= 1024.0
            return "{0:.2f} TB".format(bytes_size)
        
        # Build table rows
        rows = []
        for img in images:
            rows.append("""
                <tr>
                    <td>{0}</td>
                    <td>{1}</td>
                    <td>{2}</td>
                    <td>{3}</td>
                    <td>{4}</td>
                    <td>{5}</td>
                    <td>{6}</td>
                </tr>
            """.format(
                img.get('filename', ''),
                img.get('object_name', 'Unknown'),
                img.get('telescope_name', 'Unknown'),
                img.get('image_type', ''),
                format_size(img.get('file_size', 0)),
                img.get('download_date', '').split('T')[0],  # Date only
                img.get('file_path', '')
            ))
        
        table_rows = "\n".join(rows)
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Slooh Download Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 5px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Slooh Image Download Report</h1>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{total_images}</div>
                <div class="stat-label">Total Images</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{total_sessions}</div>
                <div class="stat-label">Download Sessions</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{total_size}</div>
                <div class="stat-label">Total Size</div>
            </div>
        </div>
        
        <p><strong>Filters Applied:</strong> {filters}</p>
        <p><strong>Images in Report:</strong> {image_count}</p>
        
        <table>
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Object</th>
                    <th>Telescope</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Date</th>
                    <th>Path</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p>Report generated: {timestamp}</p>
            <p>Slooh Image Downloader</p>
        </div>
    </div>
</body>
</html>
""".format(
            total_images=stats.get('total_images', 0),
            total_sessions=stats.get('total_sessions', 0),
            total_size=format_size(stats.get('total_bytes', 0)),
            filters=filter_text,
            image_count=len(images),
            table_rows=table_rows,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return html
    
    def export_statistics_report(self, output_path, format='html'):
        """
        Export detailed statistics report.
        
        Args:
            output_path: Path for output file
            format: Output format ('html' or 'txt')
            
        Returns:
            bool: True if successful
        """
        try:
            stats = self.tracker.get_statistics()
            
            if format == 'html':
                html = self._generate_statistics_html(stats)
                with open(output_path, 'w') as f:
                    f.write(html)
            else:
                # Text format
                text = self._generate_statistics_text(stats)
                with open(output_path, 'w') as f:
                    f.write(text)
            
            self._log('info', "Statistics report exported: {0}".format(output_path))
            return True
            
        except Exception as e:
            self._log('error', "Statistics export failed: {0}".format(str(e)))
            return False
    
    def _generate_statistics_text(self, stats):
        """Generate text statistics report"""
        lines = []
        lines.append("=" * 60)
        lines.append("SLOOH IMAGE DOWNLOAD STATISTICS")
        lines.append("=" * 60)
        lines.append("")
        lines.append("Total Images Downloaded: {0}".format(stats.get('total_images', 0)))
        lines.append("Total Download Sessions: {0}".format(stats.get('total_sessions', 0)))
        lines.append("Total Data Downloaded: {0:.2f} GB".format(
            stats.get('total_bytes', 0) / (1024.0 ** 3)))
        lines.append("")
        
        # By type
        lines.append("Downloads by Type:")
        lines.append("-" * 40)
        for img_type, count in sorted(stats.get('by_type', {}).items()):
            lines.append("  {0:10s}: {1}".format(img_type, count))
        lines.append("")
        
        # By telescope
        lines.append("Downloads by Telescope:")
        lines.append("-" * 40)
        for telescope, count in sorted(stats.get('by_telescope', {}).items()):
            lines.append("  {0:20s}: {1}".format(telescope, count))
        lines.append("")
        
        # Top objects
        lines.append("Top 10 Objects:")
        lines.append("-" * 40)
        by_object = sorted(stats.get('by_object', {}).items(), 
                          key=lambda x: x[1], reverse=True)
        for obj_name, count in by_object[:10]:
            lines.append("  {0:30s}: {1}".format(obj_name[:30], count))
        lines.append("")
        
        lines.append("=" * 60)
        lines.append("Report generated: {0}".format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        return "\n".join(lines)
    
    def _generate_statistics_html(self, stats):
        """Generate HTML statistics report"""
        # Format file size
        def format_size(bytes_size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return "{0:.2f} {1}".format(bytes_size, unit)
                bytes_size /= 1024.0
            return "{0:.2f} TB".format(bytes_size)
        
        # Build tables
        type_rows = []
        for img_type, count in sorted(stats.get('by_type', {}).items()):
            type_rows.append("<tr><td>{0}</td><td>{1}</td></tr>".format(img_type, count))
        
        telescope_rows = []
        for telescope, count in sorted(stats.get('by_telescope', {}).items()):
            telescope_rows.append("<tr><td>{0}</td><td>{1}</td></tr>".format(telescope, count))
        
        object_rows = []
        by_object = sorted(stats.get('by_object', {}).items(), 
                          key=lambda x: x[1], reverse=True)
        for obj_name, count in by_object[:15]:
            object_rows.append("<tr><td>{0}</td><td>{1}</td></tr>".format(obj_name, count))
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Slooh Download Statistics</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }}
        .summary-item {{
            text-align: center;
        }}
        .summary-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .summary-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .section {{
            margin-bottom: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Download Statistics</h1>
        
        <div class="summary">
            <div class="summary-item">
                <div class="summary-value">{total_images}</div>
                <div class="summary-label">Total Images</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{total_sessions}</div>
                <div class="summary-label">Sessions</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{total_size}</div>
                <div class="summary-label">Data Downloaded</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Downloads by Type</h2>
            <table>
                <thead>
                    <tr><th>Type</th><th>Count</th></tr>
                </thead>
                <tbody>
                    {type_rows}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Downloads by Telescope</h2>
            <table>
                <thead>
                    <tr><th>Telescope</th><th>Count</th></tr>
                </thead>
                <tbody>
                    {telescope_rows}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Top Objects (Top 15)</h2>
            <table>
                <thead>
                    <tr><th>Object</th><th>Images</th></tr>
                </thead>
                <tbody>
                    {object_rows}
                </tbody>
            </table>
        </div>
        
        <p style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 12px;">
            Report generated: {timestamp}
        </p>
    </div>
</body>
</html>
""".format(
            total_images=stats.get('total_images', 0),
            total_sessions=stats.get('total_sessions', 0),
            total_size=format_size(stats.get('total_bytes', 0)),
            type_rows="\n".join(type_rows),
            telescope_rows="\n".join(telescope_rows),
            object_rows="\n".join(object_rows),
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return html

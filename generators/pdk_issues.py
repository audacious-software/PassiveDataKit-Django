# pylint: disable=line-too-long, no-member

import os
import tempfile

import xlsxwriter

from ..models import DeviceIssue

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Reported Issues'

def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-locals, too-many-branches, too-many-statements, unused-argument
    filename = tempfile.gettempdir() + os.path.sep + 'pdk_export_issues.xlsx'

    workbook = xlsxwriter.Workbook(filename)

    sheet = workbook.add_worksheet()

    column = 0
    row = 0

    header = [
        'Source',
        'Model',
        'Manufacturer',
        'Platform',
        'User Agent',
        'State',
        'Stability Related',
        'Uptime Related',
        'Responsiveness Related',
        'Battery Use Related',
        'Power Management Related',
        'Data Volume Related',
        'Data Quality Related',
        'Bandwidth related',
        'Storage related',
        'Configuration Related',
        'Location Related',
        'Correctness Related',
        'UI Related',
        'Device Performance Related',
        'Device Stability Related',
        'Description',
        'Tags'
    ]

    for header_cell in header:
        sheet.write(row, column, header_cell)
        column += 1

    row += 1
    column = 0

    for issue in DeviceIssue.objects.all().order_by('-last_updated'):
        issue_row = []

        issue_row.append(issue.device.source.identifier)
        issue_row.append(issue.device.model.model)
        issue_row.append(issue.device.model.manufacturer)
        issue_row.append(issue.platform)
        issue_row.append(issue.user_agent)
        issue_row.append(issue.state)

        if issue.stability_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.uptime_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.responsiveness_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.battery_use_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.power_management_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.data_volume_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.data_quality_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.bandwidth_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.storage_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.configuration_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.location_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.correctness_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.ui_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.device_performance_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        if issue.device_stability_related:
            issue_row.append(True)
        else:
            issue_row.append(False)

        issue_row.append(issue.description)
        issue_row.append(issue.tags)

        for cell in issue_row:
            sheet.write(row, column, cell)
            column += 1

        row += 1
        column = 0

    workbook.close()

    return filename

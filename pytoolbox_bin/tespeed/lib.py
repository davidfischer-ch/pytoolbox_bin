# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import json, logging, os, pygal, re, time
from pytoolbox.datetime import datetime_now
from subprocess import check_output

log = logging.getLogger('isp_benchmark')

TESPEED_CSV_REGEX = re.compile(r'(?P<download>\d+\.?\d*),(?P<upload>\d+\.?\d*),"Mbit","[^"]+"')


def tespeed():
    result = None
    try:
        date_ = datetime_now()
        match = TESPEED_CSV_REGEX.match(check_output(['tespeed', '-sw']))
        if match:
            result = {k: float(v) for k, v in match.groupdict().items()}
            result.update({'date': date_})
    except Exception:
        pass
    return result


def graph(results_file, width=1920, height=1080):
    name = os.path.splitext(results_file.name)[0]
    results = sorted(json.loads(results_file.read()), key=lambda x: x['date'])

    dates = [r['date'] for r in results]
    downloads, uploads = [r['download'] for r in results], [r['upload'] for r in results]
    downloads_with_labels = [{'value': r['download'], 'label': r['date']} for r in results]
    uploads_with_labels = [{'value': r['upload'], 'label': r['date']} for r in results]

    chart = pygal.Line(width=width, height=height, order_min=0, y_title='Speed [Mbps]', range=(0, max(downloads)))
    chart.title = 'Internet access speed %s - %s' % (dates[0], dates[-1])
    chart.x_labels = [r for i, r in enumerate(dates) if i in (0, len(dates) - 1)]
    chart.add('Dowload (%0.1f)' % (sum(downloads) / len(downloads)), downloads_with_labels)
    chart.add('Upload (%0.1f)' % (sum(uploads) / len(uploads)),  uploads_with_labels)
    chart.render_to_png(name + '.png')
    chart.render_to_file(name + '.svg')


def measure(time_interval, time_range):
    start_time = time.time()
    results = []
    try:
        while True:
            counter = len(results) + 1
            time_zero = time.time()
            result = tespeed()  # {'date': datetime_now(), 'download': 100, 'upload': 10}
            result_date = result['date'] if result else datetime_now()
            log_prefix = '[%d/%d at %s] ' % (counter, time_range // time_interval + 1, result_date)
            if result:
                log.info(log_prefix + 'Download: {download} Mbps, upload: {upload} Mbps'.format(**result))
                results.append(result)
            else:
                log.warning(log_prefix + 'Unable to measure speed.')
            delta_time = time.time() - start_time
            if delta_time > time_range:
                break
            sleep_time = max(0, time_interval - (time.time() - time_zero))
            log.info(log_prefix + 'Sleeping %0.1f seconds ...' % sleep_time)
            time.sleep(sleep_time)
    except Exception as e:
        log.exception(e)
    except KeyboardInterrupt as e:
        log.warning('Operation aborted by user.')
    return results

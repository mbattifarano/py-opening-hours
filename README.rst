Opening Hours
=============

.. image:: https://app.travis-ci.com/mbattifarano/py-opening-hours.svg?branch=main
    :target: https://app.travis-ci.com/mbattifarano/py-opening-hours

A python parser for `opening hours`_.


Basic Usage
-----------

A python datetime can be evaluated against an opening hours specification
using the ``OpenHours`` class, as shown below.

.. code-block:: python

    import datetime as dt
    from py_opening_hours import OpenHours, RuleStatus

    s = "Mo-Fr 09:00-17:00; PH Off"
    hours = OpenHours.from_string(s)
    monday_at_11_am = dt.datetime(2022, 6, 6, 11, 0)
    status, comment = hours.evaluate(monday_at_11_am)
    assert status is RuleStatus.open

The ``evaluate`` method returns a ``RuleStatus`` Enum (open, closed, unknown)
along with a comment.



.. _`opening hours`: https://wiki.openstreetmap.org/wiki/Key:opening_hours


============
Installation
============

To install this project and populate the database for testing:

.. code-block:: bash

    # Make a new virtual environment
    mkvirtualenv draftkings

    # Install the requirements (only python stuff for now)
    pip install -r requires.txt

    # Run database migrations
    python draftkings/manage.py migrate

    # Load fixture data into db for testing
    python draftkings/manage.py loaddata stats.nba.com.json


The command **shortcuts**:

.. code-block:: bash

    mkvirtualenv draftkings
    make install
    make db
    make data


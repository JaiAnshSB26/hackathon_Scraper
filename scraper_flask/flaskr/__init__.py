import os
from flask import Flask, render_template

from .scraping import fetch_all_hackathons


def create_app(test_config=None):
    """Create and configure the Flask app."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/')
    def index():
        """Index route — scrape multiple sources (headless) and render results.

        The scraping logic lives in `flaskr.scraping`. Devpost uses lazy-loading
        (more items appear as you scroll), so the scraper scrolls the page to
        load additional tiles before parsing.
        """
        hackathons = fetch_all_hackathons()
        return render_template('hackathons.html', hackathons=hackathons)

    return app

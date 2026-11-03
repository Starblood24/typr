import json
from unittest.mock import Mock, PropertyMock, patch

import pytest
from textual.app import App
from textual.widgets import Static

from typr.app import TyprApp
from typr.modes.classic import ClassicConfig, generate
from typr.modes.developer import generate_snippet
from typr.modes.story import load_stories
from typr.ui.screens import (ClassicSetupScreen, ErrorScreen, HomeScreen, ResultsScreen,
                             SettingsScreen, TypingScreen)


async def test_content_read_failure_shows_retry_and_recovers(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        with patch('typr.app.generate', side_effect=OSError('missing word bank')):
            app.start_classic()
            await pilot.pause()
            assert isinstance(app.screen, ErrorScreen)
            assert app.session is None
        await pilot.press('enter')
        assert isinstance(app.screen, TypingScreen)


async def test_new_test_loading_failure_keeps_saved_result(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        app.start_classic('a', ClassicConfig(test_type='words', length=10))
        await pilot.pause()
        await pilot.press('a')
        report = app.screen
        with patch('typr.app.generate', side_effect=OSError('missing word bank')):
            await pilot.press('down', 'enter')
            assert isinstance(app.screen, ErrorScreen)
            assert app.screen.back_label == 'back'
            await pilot.press('escape')
        assert app.screen is report
        assert app.db.stats()[0]['total'] == 1


async def test_timed_extension_loading_failure_keeps_typed_text_and_retries(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        app.start_classic('a')
        await pilot.pause()
        with patch('typr.app.generate', side_effect=OSError('missing word bank')):
            await pilot.press('a')
            assert isinstance(app.screen, ErrorScreen)
            assert app.session.typed == app.original_text == 'a'
        await pilot.press('enter')
        assert isinstance(app.screen, TypingScreen)
        assert app.session.target.startswith('a ')
        assert app.original_text == app.session.target


@pytest.mark.parametrize('section', ['setup', 'settings', 'stories'])
async def test_unhandled_escape_uses_inherited_navigation(tmp_path, section):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        home = app.screen
        if section == 'stories':
            app.open_stories()
        else:
            app.push_screen(ClassicSetupScreen() if section == 'setup' else SettingsScreen())
        await pilot.pause()
        await pilot.press('escape')
        assert app.screen is home


async def test_header_uses_shared_version(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    with patch('typr.ui.screens.__version__', '9.9.9'):
        async with app.run_test():
            assert 'v9.9.9' in str(app.screen.query_one('.header', Static).content)


async def test_shutdown_tick_does_not_touch_removed_story_widgets(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        app.start_story(load_stories()[0], 1)
        await pilot.pause()
        await app.screen.query_one('.header').remove()
        with patch.object(App, 'is_running', new_callable=PropertyMock, return_value=False):
            app.tick()


async def test_escape_keeps_completed_results_open(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test() as pilot:
        app.start_classic('a', ClassicConfig(test_type='words', length=10))
        await pilot.pause()
        await pilot.press('a')
        assert isinstance(app.screen, ResultsScreen)
        await pilot.press('escape')
        assert isinstance(app.screen, ResultsScreen)
        assert app.db.stats()[0]['total'] == 1


async def test_quit_footer_survives_resize(tmp_path):
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test(size=(100, 36)) as pilot:
        await pilot.press('q')
        await pilot.resize_terminal(60, 18)
        await pilot.pause()
        assert app.screen.quitting
        assert str(app.screen.query_one('.footer', Static).content) == 'y confirm   n cancel   esc cancel'
        await pilot.press('escape')
        assert isinstance(app.screen, HomeScreen) and not app.screen.quitting


async def test_settings_reject_values_from_another_setting(tmp_path):
    from typr.storage.database import Database
    db = Database(tmp_path/'typr.db')
    db.setting('ascii art', 'subtle')
    db.setting('animations', 'on')
    db.close()
    app = TyprApp(tmp_path, skip_boot=True)
    async with app.run_test():
        assert app.settings['ascii art'] == 'on'
        assert app.settings['animations'] == 'subtle'


@pytest.mark.parametrize('kind', ['words', 'snippets', 'stories'])
def test_malformed_content_raises_actionable_value_error(kind):
    if kind == 'words':
        with patch('typr.modes.classic.files') as files:
            files.return_value.joinpath.return_value.read_text.return_value = json.dumps({'common': []})
            with pytest.raises(ValueError):
                generate(ClassicConfig())
    elif kind == 'snippets':
        with patch('typr.modes.developer.files') as files:
            files.return_value.joinpath.return_value.read_text.return_value = json.dumps({'python': []})
            with pytest.raises(ValueError):
                generate_snippet('python')
    else:
        file = Mock(name='story.json')
        file.name = 'story.json'
        file.read_text.return_value = json.dumps(dict(id='one', title='one', language='en', chapters=['bad chapter']))
        with patch('typr.modes.story.files') as files:
            files.return_value.joinpath.return_value.joinpath.return_value.iterdir.return_value = [file]
            with pytest.raises(ValueError):
                load_stories()


@pytest.mark.parametrize('field,value', [('art', {}), ('intro', 8), ('title', '\x1b[2J'), ('paragraphs', [' '])])
def test_invalid_chapter_metadata_is_rejected_before_rendering(field, value):
    chapter = dict(title='chapter', paragraphs=['text'])
    chapter[field] = value
    file = Mock()
    file.name = 'story.json'
    file.read_text.return_value = json.dumps(dict(id='one', title='one', language='en', chapters=[chapter]))
    with patch('typr.modes.story.files') as files:
        files.return_value.joinpath.return_value.joinpath.return_value.iterdir.return_value = [file]
        with pytest.raises(ValueError):
            load_stories()

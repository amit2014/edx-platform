# disable missing docstring
# pylint: disable=C0111

import os
from lettuce import world, step

from django.conf import settings

from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from splinter.request_handler.request_handler import RequestHandler

TEST_ROOT = settings.COMMON_TEST_DATA_ROOT

# We should wait 300 ms for event handler invocation + 200ms for safety.
DELAY = 0.5

ERROR_MESSAGES = {
    'url_format': u'Incorrect url format.',
    'file_type': u'Link types should be unique.',
}

STATUSES = {
    'found': u'Timed Transcript Found',
    'not found': u'No Timed Transcript',
    'replace': u'Timed Transcript Conflict',
    'uploaded_successfully': u'Timed Transcript uploaded successfully',
    'use existing': u'Timed Transcript Not Updated',
}

SELECTORS = {
    'error_bar': '.transcripts-error-message',
    'url_inputs': '.videolist-settings-item input.input',
    'collapse_link': '.collapse-action.collapse-setting',
    'collapse_bar': '.videolist-extra-videos',
    'status_bar': '.transcripts-message-status',
}

# button type , button css selector, button message
TRANSCRIPTS_BUTTONS = {
    'import': ('.setting-import',  'Import from YouTube'),
    'download_to_edit': ('.setting-download', 'Download to Edit'),
    'disabled_download_to_edit': ('.setting-download.is-disabled', 'Download to Edit'),
    'upload_new_timed_transcripts': ('.setting-upload',  'Upload New Timed Transcript'),
    'replace': ('.setting-replace', 'Yes, Replace EdX Timed Transcript with YouTube Timed Transcript'),
    'choose': ('.setting-choose', 'Timed Transcript from {}'),
    'use_existing': ('.setting-use-existing', 'Use Existing Timed Transcript'),
}


def _clear_field(index):
    world.css_fill(SELECTORS['url_inputs'], '', index)
    # In some reason chromeDriver doesn't trigger 'input' event after filling
    # field by an empty value. That's why we trigger it manually via jQuery.
    world.trigger_event(SELECTORS['url_inputs'], event='input', index=index)


@step('I clear fields$')
def clear_fields(_step):
    js_str = '''
        $('{selector}')
            .eq({index})
            .prop('disabled', false)
            .removeClass('is-disabled');
    '''
    for index in range(1, 4):
        js = js_str.format(selector=SELECTORS['url_inputs'], index=index - 1)
        world.browser.execute_script(js)
        _clear_field(index)

    world.wait(DELAY)
    world.wait_for_ajax_complete()


@step('I clear field number (.+)$')
def clear_field(_step, index):
    index = int(index) - 1
    _clear_field(index)
    world.wait(DELAY)
    world.wait_for_ajax_complete()


@step('I expect (.+) inputs are disabled$')
def inputs_are_disabled(_step, indexes):
    index_list = [int(i.strip()) - 1 for i in indexes.split(',')]
    for index in index_list:
        el = world.css_find(SELECTORS['url_inputs'])[index]

        assert el['disabled']


@step('I expect inputs are enabled$')
def inputs_are_enabled(_step):
    for index in range(3):
        el = world.css_find(SELECTORS['url_inputs'])[index]

        assert not el['disabled']


@step('I do not see error message$')
def i_do_not_see_error_message(_step):
    assert not world.css_visible(SELECTORS['error_bar'])


@step('I see error message "([^"]*)"$')
def i_see_error_message(_step, error):
    assert world.css_has_text(SELECTORS['error_bar'], ERROR_MESSAGES[error.strip()])


@step('I do not see status message$')
def i_do_not_see_status_message(_step):
    assert not world.css_visible(SELECTORS['status_bar'])


@step('I see status message "([^"]*)"$')
def i_see_status_message(_step, status):
    assert not world.css_visible(SELECTORS['error_bar'])
    assert world.css_has_text(SELECTORS['status_bar'], STATUSES[status.strip()])

    DOWNLOAD_BUTTON = TRANSCRIPTS_BUTTONS["download_to_edit"][0]
    if world.is_css_present(DOWNLOAD_BUTTON, wait_time=1) \
    and not world.css_find(DOWNLOAD_BUTTON)[0].has_class('is-disabled'):
        assert _transcripts_are_downloaded()


@step('I (.*)see button "([^"]*)"$')
def i_see_button(_step, not_see, button_type):
    button = button_type.strip()

    if not_see.strip():
        assert world.is_css_not_present(TRANSCRIPTS_BUTTONS[button][0])
    else:
        assert world.css_has_text(TRANSCRIPTS_BUTTONS[button][0], TRANSCRIPTS_BUTTONS[button][1])


@step('I (.*)see (.*)button "([^"]*)" number (\d+)$')
def i_see_button_with_custom_text(_step, not_see, button_type, custom_text, index):
    button = button_type.strip()
    custom_text = custom_text.strip()
    index = int(index.strip()) - 1

    if not_see.strip():
        assert world.is_css_not_present(TRANSCRIPTS_BUTTONS[button][0])
    else:
        assert world.css_has_text(TRANSCRIPTS_BUTTONS[button][0], TRANSCRIPTS_BUTTONS[button][1].format(custom_text), index)


@step('I click transcript button "([^"]*)"$')
def click_button_transcripts_variant(_step, button_type):
    button = button_type.strip()
    world.css_click(TRANSCRIPTS_BUTTONS[button][0])
    world.wait_for_ajax_complete()


@step('I click transcript button "([^"]*)" number (\d+)$')
def click_button_index(_step, button_type, index):
    button = button_type.strip()
    index = int(index.strip()) - 1

    world.css_click(TRANSCRIPTS_BUTTONS[button][0], index)
    world.wait_for_ajax_complete()


@step('I remove "([^"]+)" transcripts id from store')
def remove_transcripts_from_store(_step, subs_id):
    """Remove from store, if transcripts content exists."""
    filename = 'subs_{0}.srt.sjson'.format(subs_id.strip())
    content_location = StaticContent.compute_location(
        world.scenario_dict['COURSE'].org,
        world.scenario_dict['COURSE'].number,
        filename
    )
    try:
        content = contentstore().find(content_location)
        contentstore().delete(content.get_id())
        print('Transcript file was removed from store.')
    except NotFoundError:
        print('Transcript file was NOT found and not removed.')


@step('I enter a "([^"]+)" source to field number (\d+)$')
def i_enter_a_source(_step, link, index):
    index = int(index) - 1

    if index is not 0 and not world.css_visible(SELECTORS['collapse_bar']):
        world.css_click(SELECTORS['collapse_link'])

        assert world.css_visible(SELECTORS['collapse_bar'])

    world.css_fill(SELECTORS['url_inputs'], link, index)
    world.wait(DELAY)
    world.wait_for_ajax_complete()


@step('I upload the transcripts file "([^"]*)"$')
def upload_file(_step, file_name):
    path = os.path.join(TEST_ROOT, 'uploads/', file_name.strip())
    world.browser.execute_script("$('form.file-chooser').show()")
    world.browser.attach_file('file', os.path.abspath(path))
    world.wait_for_ajax_complete()


@step('I see "([^"]*)" text in the captions')
def check_text_in_the_captions(_step, text):
    assert world.browser.is_text_present(text.strip(), 5)


@step('I see value "([^"]*)" in the field "([^"]*)"$')
def check_transcripts_field(_step, values, field_name):
    world.click_link_by_text('Advanced')
    field_id = '#' + world.browser.find_by_xpath('//label[text()="%s"]' % field_name.strip())[0]['for']
    values_list = [i.strip() == world.css_value(field_id) for i in values.split('|')]
    assert any(values_list)
    world.click_link_by_text('Basic')


@step('I save changes$')
def save_changes(_step):
    save_css = 'a.save-button'
    world.css_click(save_css)
    world.wait_for_ajax_complete()


@step('I open tab "([^"]*)"$')
def open_tab(_step, tab_name):
    world.click_link_by_text(tab_name.strip())
    world.wait_for_ajax_complete()


@step('I set value "([^"]*)" to the field "([^"]*)"$')
def set_value_transcripts_field(_step, value, field_name):
    field_id = '#' + world.browser.find_by_xpath('//label[text()="%s"]' % field_name.strip())[0]['for']
    world.css_fill(field_id, value.strip())
    world.wait_for_ajax_complete()


@step('I revert the transcript field "([^"]*)"$')
def revert_transcripts_field(_step, field_name):
    world.revert_setting_entry(field_name)


def _transcripts_are_downloaded():
    world.wait_for_ajax_complete()
    request = RequestHandler()
    DOWNLOAD_BUTTON = world.css_find(TRANSCRIPTS_BUTTONS["download_to_edit"][0]).first
    url = DOWNLOAD_BUTTON['href']
    request.connect(url)

    return request.status_code.is_success()

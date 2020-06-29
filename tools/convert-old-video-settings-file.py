#!/usr/bin/env python3
"""Convert legacy video formats to generate gstreamer pipeline
    Move old files, such as vidformat and gstreamer2 parameter files
    to the user trash folder.
"""

import os
import subprocess
import sys


def merge_gst_elements(elements: list):
    """A simple helper to merge gstreamer elements in pipeline format

    Args:
        elements (list): List that contains gstreamer elements

    Returns:
        str: Final gstreamer pipeline
    """

    return ' ! '.join(elements)


class Convert:
    """Convert main class
        Check file description for more information
    """

    HOME = os.path.expanduser('~')
    TRASH = os.path.join(HOME, '.local/share/Trash/files')
    vidformat_file = os.path.join(HOME, 'vidformat.param')
    gstreamer2_file = os.path.join(HOME, 'gstreamer2.param')

    device_settings = {
        'device': '/dev/video0',
        'width': 1920,
        'height': 1080,
        'framerate': 30,
    }

    SOURCE_PIPELINE = merge_gst_elements([
        'v4l2src device={device} do-timestamp=true',
        'video/x-h264, width={width}, height={height}, framerate={framerate}/1',
    ])

    PARSE_PIPELINE = merge_gst_elements([
        'h264parse',
        'queue',
        'rtph264pay config-interval=10 pt=96',
        'udpsink host=192.168.2.1 port=5600',
    ])

    def update_configuration(self, pair: tuple):
        """Update class internal configuration about video source and resolution

        Args:
            pair (tuple): Tuple that contains (key, value) for pipeline
            settings dict
        """

        (key, value) = pair
        self.device_settings[key] = value

    @staticmethod
    def create_source_element(device='/dev/video0', width=1920, height=1080, framerate=30):
        """Populate and generate gstreamer v4l2src pipeline

        Args:
            device (str, optional): Video device. Defaults to '/dev/video0'.
            width (int, optional): Video width. Defaults to 1920.
            height (int, optional): Video height. Defaults to 1080.
            framerate (int, optional): Video framerate. Defaults to 30.

        Returns:
            str: Return string with the pipeline
        """

        return Convert.SOURCE_PIPELINE.format(
            device=device,
            width=width,
            height=height,
            framerate=framerate
        )

    @staticmethod
    def read_content_then_trash_file(filepath: str):
        """Get content from file and move it to the trash

        Args:
            filepath (str): Path for the parameter file

        Returns:
            str: File content
        """

        if not os.path.isfile(filepath):
            return None

        file_object = open(filepath, 'r')
        content = file_object.read()
        file_object.close()

        filename = os.path.basename(filepath)
        os.rename(filepath, os.path.join(Convert.TRASH, filename))

        return content

    def run(self):
        """Run and extract pipeline from parameter files

        Returns:
            str: Final gstreamer pipeline
        """

        # Create trash folder if does not exist
        try:
            os.makedirs(self.TRASH)
        except FileExistsError:
            pass

        # Get files content
        vidformat_file_content = self.read_content_then_trash_file(
            self.vidformat_file)
        gstreamer2_file_content = self.read_content_then_trash_file(
            self.gstreamer2_file)

        # Get content of each setting file
        # Extract the necessary information to build our new pipeline
        if vidformat_file_content:
            lines = vidformat_file_content.split('\n')
            for name, value in zip(['width', 'height', 'framerate', 'device'], lines):
                if name != 'device':
                    self.update_configuration((name, int(value)))
                else:
                    self.update_configuration((name, value))

        user_parse_pipeline = ''
        if gstreamer2_file_content:
            # Break each line as a pipeline element
            # And join all elements to create a pipeline
            elements = gstreamer2_file_content.replace('\n', '').split('!')
            elements = [element.strip() for element in elements]
            elements = list(filter(lambda element: element != '', elements))
            user_parse_pipeline = merge_gst_elements(elements).strip()

        parse_pipeline = Convert.PARSE_PIPELINE
        if user_parse_pipeline not in parse_pipeline:
            parse_pipeline = user_parse_pipeline

        source_pipeline = Convert.create_source_element(
            **self.device_settings)
        return merge_gst_elements([source_pipeline, parse_pipeline])


if __name__ == "__main__":
    converter = Convert()

    # Get pipeline
    pipeline = converter.run()

    # Create a pipeline to test the created one
    test_pipeline = pipeline.replace('!', 'num-buffers=1 !', 1)
    result = subprocess.call(['gst-launch-1.0 ' + test_pipeline], shell=True)
    if(result != 0):
        print('Failed to run pipeline: {}'.format(pipeline))
        sys.exit(1)

    print("Final pipeline: {}".format(pipeline))
    # Create settings file for camera-manager
    settings = """
mavlink_endpoint = "udpbcast:192.168.0.255:14550"

[[videos_configuration]]
device = "/dev/video0"
pipeline = "{}"
endpoint = "rtsp://192.168.0.104:8554/video1"

[header]
name = "Camera Manager"
version = 0""".format(pipeline)

    home = os.path.expanduser('~')
    path = os.path.join(home, '.config/mavlink-camera-manager/')
    filename = os.path.join(path, 'server-settings.toml')

    if os.path.isfile(filename):
        print("Settings file already exist ({}), abort!".format(filename))
        sys.exit(2)

    if not os.path.exists(path):
        os.makedirs(path)

    try:
        with open(filename, "w") as file:
            file.write(settings)
            file.close()
    except Exception as error:
        print("Something is wrong: {}".format(error))
        sys.exit(3)

    sys.exit(0)

import os
import ffmpeg
import re
import json

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
WORK_PATH = os.path.join(ROOT_PATH, 'video')
OUTPUT_PATH = os.path.join(ROOT_PATH, 'Output_file')
VIDEO_MAP = {
    'VIDEO_PATH': None,
    'AUDIO_PATH': None,
    'VIDEO_TITLE': None,
    'VIDEO_NUM': None,
    'GROUP_TITLE': None,
    'OUTPUT_FILE': None
}


class Build:
    files_list = []

    def get_info_file(file_id):

        info_file_path = os.path.join(WORK_PATH, str(file_id), '.videoInfo')

        with open(info_file_path, 'r+', encoding='utf-8') as f:
            s = f.read()
            if '\'' in s:
                tmp_file = os.path.join(WORK_PATH, str(file_id), 'tmp')
                with open(tmp_file, 'w', encoding='utf-8') as tmp:
                    tmp.write(
                        s.replace('\'',
                                  '\"').replace('True', '\"True\"').replace(
                                      'False', '\"False\"'))
                Build.read_json(tmp_file)
                os.remove(tmp_file)
            else:
                Build.read_json(info_file_path)

    def video_file_process(file_id):

        path = os.path.join(WORK_PATH, str(file_id))
        for files in os.listdir(path):
            files_path = os.path.join(path, files)
            files_video_name_pattern = r"^.*?-30080.m4s$"
            files_audio_name_pattern = r"^.*?-30280.m4s$"
            files_video_name = re.compile(files_video_name_pattern)
            files_audio_name = re.compile(files_audio_name_pattern)

            if files_video_name.match(files_path):
                Build.files_list.append(files_path)

            elif files_audio_name.match(files_path):
                Build.files_list.append(files_path)
        Build.m4s_files_process(Build.files_list)

    def m4s_files_process(m4s_files_list):
        video_tmp = os.path.join(os.path.dirname(m4s_files_list[0]),
                                 'video_tmp.m4s')
        audio_tmp = os.path.join(os.path.dirname(m4s_files_list[1]),
                                 'audio_tmp.m4s')
        VIDEO_MAP['VIDEO_PATH'] = video_tmp
        VIDEO_MAP['AUDIO_PATH'] = audio_tmp
        for m4s_file_path in m4s_files_list:
            try:
                with open(m4s_file_path, '+rb') as f:
                    head = f.read()[0:32]
                    f.seek(0)
                    end = f.read()[32:]
                    head = re.sub(b'000000000', b'', head)
                    head = re.sub(b'avc1', b'', head)
                    head = re.sub(b'\\$', b' ', head)

                    files = head + end
                    if '30080' in m4s_file_path:
                        with open(video_tmp, 'w+b') as tmp:
                            tmp.write(files)
                    elif '30280' in m4s_file_path:
                        with open(audio_tmp, 'w+b') as tmp:
                            tmp.write(files)

            except Exception as e:
                print("m4s文件错误： " + str(e))
        Build.ffmpeg_process(VIDEO_MAP['VIDEO_PATH'], VIDEO_MAP['AUDIO_PATH'])

    def ffmpeg_process(video_path, audio_path):

        video_stream = ffmpeg.input(video_path)
        audio_stream = ffmpeg.input(audio_path)
        output_path = os.path.join(
            OUTPUT_PATH,
            VIDEO_MAP['GROUP_TITLE'],
        )
        output_path = os.path.join(output_path, VIDEO_MAP['OUTPUT_FILE'])

        output_stream = ffmpeg.output(
            video_stream,
            audio_stream,
            output_path,
            vcodec='copy',
        )

        def count_none(Map):
            Nones = sum(values is None for values in Map.values())
            if Nones > 0:
                return False
            else:
                return True

        if count_none(VIDEO_MAP):
            Build.makedir(output_path)
            ffmpeg.run(output_stream)

        # ffmpeg.overwrite_output(output_stream)
        # ffmpeg.run(output_stream)

    def makedir(path):
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            pass

    def read_json(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            info_file = json.load(f)
            VIDEO_MAP['VIDEO_NUM'] = info_file.get('p')  # P标号
            VIDEO_MAP['VIDEO_TITLE'] = info_file.get('title')  # 视频名称
            VIDEO_MAP['OUTPUT_FILE'] = 'P' + str(
                VIDEO_MAP['VIDEO_NUM']) + '_' + str(
                    VIDEO_MAP['VIDEO_TITLE']) + '.mp4'  # 输出视频名称
            VIDEO_MAP['GROUP_TITLE'] = info_file.get('groupTitle').replace(
                ' ', '')  # 视频组名称

    def build():

        Build.makedir(ROOT_PATH)
        Build.makedir(WORK_PATH)
        Build.makedir(OUTPUT_PATH)
        if os.listdir(WORK_PATH) == []:
            print('工作目录为空')
        else:
            for file_id in os.listdir(WORK_PATH):
                Build.get_info_file(file_id)
                Build.video_file_process(file_id)


if __name__ == '__main__':
    bu = Build
    bu.build()

import os
import subprocess
import time
from pydub import AudioSegment
from pydub.silence import split_on_silence
import numpy as np

# 必要なディレクトリの確認と作成
for dir in ['./input', './output', './setting', './artWork']:
    if not os.path.exists(dir):
        os.makedirs(dir)

def remove_silence(audio, min_silence_len=2000, silence_thresh=-40, target_silence_len=1000):
    """
    2秒以上の無音部分を1秒の無音に短縮する関数
    
    :param audio: 処理する AudioSegment オブジェクト
    :param min_silence_len: 無音と判断する最小の長さ（ミリ秒）
    :param silence_thresh: 無音と判断する音量閾値（dB）
    :param target_silence_len: 短縮後の無音の長さ（ミリ秒）
    :return: 処理された AudioSegment オブジェクト
    """
    chunks = split_on_silence(
        audio, 
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=0  # 無音部分を完全に分割
    )
    
    processed_chunks = [chunks[0]]
    for chunk in chunks[1:]:
        silence_chunk = AudioSegment.silent(duration=target_silence_len)
        processed_chunks.append(silence_chunk)
        processed_chunks.append(chunk)
    
    return sum(processed_chunks)

def apply_eq(input_file, output_file):
    # EQ設定の適用
    with open('./setting/eq.txt', 'r') as f:
        eq_settings = f.read().strip().split('\n')
    
    eq_filter = ','.join([f"equalizer=f={freq}:width_type=o:width=1:g={gain}" for freq, gain in [line.split(',') for line in eq_settings]])
    
    command = [
        'ffmpeg', '-i', input_file,
        '-af', eq_filter,
        '-c:a', 'pcm_s16le',
        output_file
    ]
    
    subprocess.run(command, check=True)

def process_audio(input_file, silence_settings):
    start_time = time.time()
    print(f"処理を開始します... 開始時間: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # 入力ファイルの読み込み
    print("音声ファイルを読み込んでいます...")
    audio = AudioSegment.from_wav(input_file)

    # 無音部分の処理
    print("無音部分を処理しています...")
    audio = remove_silence(audio, **silence_settings)

    # 一時的なWAVファイルとして保存
    temp_wav = './temp_processed.wav'
    audio.export(temp_wav, format='wav')

    # ラウドネスノーマライズとEQ処理
    print("ラウドネスノーマライズとEQ処理を適用しています...")
    temp_eq_wav = './temp_eq.wav'
    apply_eq(temp_wav, temp_eq_wav)

    # MP3への変換とメタデータの追加
    print("MP3に変換し、メタデータを追加しています...")
    output_file = './output/processed_output.mp3'
    
    # タグ情報の読み込み
    with open('./setting/tag.txt', 'r', encoding='utf-8') as f:
        tag_data = dict(line.strip().split('=') for line in f)

    # FFmpegコマンドの構築
    command = [
        'ffmpeg', '-i', temp_eq_wav,
        '-i', './artWork/artwork.jpg',
        '-filter:a', f"loudnorm=I=-16.0:LRA=11:TP=-1.5",
        '-c:a', 'libmp3lame', '-b:a', '96k',
        '-map', '0:0', '-map', '1:0',
        '-id3v2_version', '3',
        '-metadata', f"title={tag_data['タイトル']}",
        '-metadata', f"album={tag_data['アルバム']}",
        '-metadata', f"year={tag_data['年']}",
        '-metadata', f"genre={tag_data['ジャンル']}",
        '-metadata', f"artist={tag_data['参加アーティスト']}",
        '-metadata', f"track={tag_data['トラック番号']}",
        output_file
    ]

    subprocess.run(command, check=True)

    # 一時ファイルの削除
    os.remove(temp_wav)
    os.remove(temp_eq_wav)

    end_time = time.time()
    processing_time = end_time - start_time
    print(f"処理が完了しました。出力ファイル: {output_file}")
    print(f"終了時間: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    print(f"処理時間: {processing_time:.2f} 秒")

# メイン処理
if __name__ == "__main__":
    overall_start_time = time.time()
    print(f"全体の処理を開始します... 開始時間: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(overall_start_time))}")

    # 無音処理の設定
    silence_settings = {
        'min_silence_len': 2000,  # 2秒以上の無音を処理対象とする
        'silence_thresh': -60,    # 無音と判断する音量閾値（dB）
        'target_silence_len': 1000  # 短縮後の無音の長さ（1秒）
    }

    input_files = [f for f in os.listdir('./input') if f.endswith('.wav')]
    for input_file in input_files:
        process_audio(os.path.join('./input', input_file), silence_settings)

    overall_end_time = time.time()
    overall_processing_time = overall_end_time - overall_start_time
    print(f"全体の処理が完了しました。")
    print(f"終了時間: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(overall_end_time))}")
    print(f"全体の処理時間: {overall_processing_time:.2f} 秒")

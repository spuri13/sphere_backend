
import whisper
import librosa
import os



audio_path = "C:/Users/praga/Videos/TranscribeVideo.mp3"
audio=librosa.load(audio_path)
print(audio)

if not os.path.exists("audio_batches"):
    os.makedirs("audio_batches")

list=[]

start = 0
end = 10000
incremention = 10000

# print(len(audio)%10000)
iterations_num = len(audio)//10000 + 1

for i in range(iterations_num):
    print(i)
    frame=audio[start:end]
    start+=incremention
    end+=incremention
    # list.append(frame)
    print(frame)



# print(list)


# currentFrame = 0
# time = 1.0

# if not os.path.exists("frame_images"):
#     os.makedirs("frame_images")

# while True:
#     vid.read()



# model = whisper.load_model("base")
# result = model.transcribe(audio_path, fp16=False)
# # print(result['segments'][0]['start'])
# print(result["text"])






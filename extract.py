import vpk, pydub

def extract(path, lang, sounds, temp):
    pak = None if lang == 'english' else vpk.open(f"{path}/portal2_{lang}/pak01_dir.vpk")
    pak_fallback = vpk.open(f"{path}/portal2/pak01_dir.vpk")
    def get_pak(path):
        if pak is not None and path in pak:
            return pak.get_file(path)
        else:
            return pak_fallback.get_file(path)

    res = {}
    for dir in sounds.keys():
        i = 0
        for files in sounds[dir]:
            files = files.split(":")
            i += 1
            open(f"{temp}/temp.wav", "wb").write(get_pak(files[0]).read())
            pydub.AudioSegment.converter = f"{temp}/ffmpeg.exe"
            sound = pydub.AudioSegment.from_wav(f"{temp}/temp.wav")
            for file in files[1:]:
                open(f"{temp}/temp.wav", "wb").write(get_pak(file.split("@")[0]).read())
                sound = sound.append(pydub.AudioSegment.from_wav(f"{temp}/temp.wav"), crossfade=int(file.split("@")[1]))
            sound.export(f"{temp}/temp.mp3", format="mp3", parameters=["-ac", "1", "-b:a", "40k"])
            res[f"{dir}/{i:03}.mp3"] = open(f"{temp}/temp.mp3", "rb").read()
    return res
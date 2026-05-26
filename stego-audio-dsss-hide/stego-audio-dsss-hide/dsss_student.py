#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import wave
import struct
import math
import random
import argparse

def generate_pn_sequence(seed_val, length):
    pass

def embed_message(cover_samples, message_str, seed_val, alpha):
    pass

def extract_message(stego_samples, num_bits, seed_val):
    pass

def calculate_snr(cover_samples, stego_samples):
    pass

def add_noise(stego_samples, variance):
    noisy_samples = []
    std_dev = math.sqrt(variance)
    for sample in stego_samples:
        noise = random.gauss(0, std_dev)
        noisy_val = sample + noise
        noisy_val = max(-1.0, min(1.0, noisy_val))
        noisy_samples.append(noisy_val)
    return noisy_samples

def read_wav(filename):
    with wave.open(filename, 'rb') as wav:
        params = wav.getparams()
        nframes = wav.getnframes()
        frames = wav.readframes(nframes)
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
            print("Loi: Chi ho tro file WAV 16-bit Mono!")
            sys.exit(1)
        samples = list(struct.unpack(f'<{nframes}h', frames))
        float_samples = [s / 32768.0 for s in samples]
        return float_samples, params

def write_wav(filename, float_samples, params):
    with wave.open(filename, 'wb') as wav:
        wav.setparams(params)
        int_samples = []
        for s in float_samples:
            ival = int(s * 32767.0)
            ival = max(-32768, min(32767, ival))
            int_samples.append(ival)
        frames = struct.pack(f'<{len(int_samples)}h', *int_samples)
        wav.writeframes(frames)

def main():
    parser = argparse.ArgumentParser(description="DSSS Audio Steganography Lab Tool")
    subparsers = parser.add_subparsers(dest="command", help="Lenh thuc hien")

    # Command: gen-pn
    parser_pn = subparsers.add_parser("gen-pn", help="Sinh chuoi ma gia ngau nhien PN")
    parser_pn.add_argument("--seed", type=int, required=True, help="Gia tri Seed (1-1023)")
    parser_pn.add_argument("--length", type=int, required=True, help="Do dai chuoi PN")
    parser_pn.add_argument("--out", type=str, required=True, help="File ket qua luu chuoi PN")

    # Command: embed
    parser_emb = subparsers.add_parser("embed", help="Nhung thong diep vao file am thanh")
    parser_emb.add_argument("--cover", type=str, required=True, help="File am thanh goc cover.wav")
    parser_emb.add_argument("--message", type=str, required=True, help="Thong diep bi mat (ASCII)")
    parser_emb.add_argument("--seed", type=int, required=True, help="Khoa Seed (1-1023)")
    parser_emb.add_argument("--alpha", type=float, default=0.005, help="He so tang ich alpha")
    parser_emb.add_argument("--out", type=str, required=True, help="File am thanh sau nhung stego.wav")

    # Command: extract
    parser_ext = subparsers.add_parser("extract", help="Giai ma thong diep tu file am thanh")
    parser_ext.add_argument("--stego", type=str, required=True, help="File am thanh stego.wav")
    parser_ext.add_argument("--bits", type=int, default=32, help="So luong bit can giai ma (mac dinh 32 bit = 4 ky tu)")
    parser_ext.add_argument("--seed", type=int, required=True, help="Khoa Seed (1-1023)")
    parser_ext.add_argument("--out", type=str, required=True, help="File ket qua luu thong diep khoi phuc")

    # Command: snr
    parser_snr = subparsers.add_parser("snr", help="Tinh toan ty so SNR")
    parser_snr.add_argument("--cover", type=str, required=True, help="File cover.wav")
    parser_snr.add_argument("--stego", type=str, required=True, help="File stego.wav")
    parser_snr.add_argument("--out", type=str, required=True, help="File ket qua luu gia tri SNR")

    # Command: add-noise
    parser_noise = subparsers.add_parser("add-noise", help="Them nhieu vao file am thanh stego")
    parser_noise.add_argument("--stego", type=str, required=True, help="File stego.wav")
    parser_noise.add_argument("--variance", type=float, required=True, help="Phuong sai nhieu")
    parser_noise.add_argument("--out", type=str, required=True, help="File dau ra am thanh co nhieu noisy.wav")

    args = parser.parse_args()

    if args.command == "gen-pn":
        pn = generate_pn_sequence(args.seed, args.length)
        if pn is None:
            print("Ham generate_pn_sequence chua duoc cai dat!")
            return
        with open(args.out, "w") as f:
            f.write(" ".join(map(str, pn)))
        print(f"Da luu chuoi PN vao {args.out}")

    elif args.command == "embed":
        cover, params = read_wav(args.cover)
        stego = embed_message(cover, args.message, args.seed, args.alpha)
        if stego is None:
            print("Ham embed_message chua duoc cai dat!")
            return
        write_wav(args.out, stego, params)
        print(f"Da nhung thong diep va luu thanh cong vao {args.out}")

    elif args.command == "extract":
        stego, _ = read_wav(args.stego)
        recovered = extract_message(stego, args.bits, args.seed)
        if recovered is None:
            print("Ham extract_message chua duoc cai dat!")
            return
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(recovered)
        print(f"Da khoi phuc thong diep va luu vao {args.out}: {recovered}")

    elif args.command == "snr":
        cover, _ = read_wav(args.cover)
        stego, _ = read_wav(args.stego)
        snr = calculate_snr(cover, stego)
        if snr is None:
            print("Ham calculate_snr chua duoc cai dat!")
            return
        with open(args.out, "w") as f:
            f.write(f"{snr:.4f}")
        print(f"Da tinh toan SNR va luu vao {args.out}: {snr:.4f} dB")

    elif args.command == "add-noise":
        stego, params = read_wav(args.stego)
        noisy = add_noise(stego, args.variance)
        write_wav(args.out, noisy, params)
        print(f"Da them nhieu phuong sai {args.variance} va luu vao {args.out}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

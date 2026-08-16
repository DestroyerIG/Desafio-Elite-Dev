"use client";

import jsQR from "jsqr";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorMessage } from "@/components/ui/feedback";


export function QrScanner({
  disabled,
  onScan,
}: {
  disabled: boolean;
  onScan: (value: string) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameRef = useRef<number | null>(null);
  const onScanRef = useRef(onScan);
  const [isActive, setIsActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  useEffect(() => {
    onScanRef.current = onScan;
  }, [onScan]);

  const stopCamera = useCallback(() => {
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsActive(false);
  }, []);

  useEffect(() => stopCamera, [stopCamera]);

  async function startCamera() {
    setCameraError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError(
        "Este navegador não oferece acesso à câmera. Use o código manual.",
      );
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      const video = videoRef.current;
      if (!video) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;
      video.srcObject = stream;
      await video.play();
      setIsActive(true);
      scanFrame();
    } catch (error) {
      const message =
        error instanceof DOMException && error.name === "NotAllowedError"
          ? "Permissão da câmera negada. Autorize-a ou use o código manual."
          : "Não foi possível iniciar a câmera. Use o código manual.";
      setCameraError(message);
      stopCamera();
    }
  }

  function scanFrame() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || !streamRef.current) return;

    if (
      video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA &&
      video.videoWidth > 0 &&
      video.videoHeight > 0
    ) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext("2d", { willReadFrequently: true });
      if (context) {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const image = context.getImageData(0, 0, canvas.width, canvas.height);
        const result = jsQR(image.data, image.width, image.height, {
          inversionAttempts: "attemptBoth",
        });
        if (result?.data) {
          stopCamera();
          onScanRef.current(result.data);
          return;
        }
      }
    }
    frameRef.current = requestAnimationFrame(scanFrame);
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-slate-950 p-4 text-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">Leitor de QR Code</h2>
          <p className="mt-1 text-sm text-slate-300">
            A leitura acontece somente neste dispositivo.
          </p>
        </div>
        {isActive ? (
          <Button type="button" variant="secondary" onClick={stopCamera}>
            Parar câmera
          </Button>
        ) : (
          <Button type="button" disabled={disabled} onClick={startCamera}>
            Abrir câmera
          </Button>
        )}
      </div>

      <div className="relative mt-4 aspect-video overflow-hidden rounded-lg border border-slate-700 bg-black">
        <video
          ref={videoRef}
          muted
          playsInline
          className="h-full w-full object-cover"
        />
        {!isActive && (
          <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-sm text-slate-400">
            Abra a câmera e enquadre o QR do ingresso.
          </div>
        )}
        {isActive && (
          <div
            aria-hidden
            className="pointer-events-none absolute inset-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-xl border-2 border-white shadow-[0_0_0_999px_rgba(0,0,0,0.35)]"
          />
        )}
      </div>
      <canvas ref={canvasRef} className="hidden" />
      {cameraError && <ErrorMessage message={cameraError} className="mt-4" />}
    </section>
  );
}

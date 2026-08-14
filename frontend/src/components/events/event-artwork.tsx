import Image from "next/image";

export function EventArtwork({
  imageUrl,
  title,
  className = "h-48",
}: {
  imageUrl: string | null;
  title: string;
  className?: string;
}) {
  if (!imageUrl) {
    return (
      <div
        className={`${className} flex items-center justify-center bg-slate-100 px-6 text-center text-sm text-slate-500`}
      >
        Imagem não disponível
      </div>
    );
  }

  return (
    <div className={`${className} relative overflow-hidden bg-slate-100`}>
      <Image
        src={imageUrl}
        alt={`Imagem do evento ${title}`}
        fill
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        className="object-cover"
      />
    </div>
  );
}


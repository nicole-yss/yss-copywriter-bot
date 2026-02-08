"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ContentTypeSelectorProps {
  contentType: string;
  onContentTypeChange: (value: string) => void;
  platform: string;
  onPlatformChange: (value: string) => void;
}

export function ContentTypeSelector({
  contentType,
  onContentTypeChange,
  platform,
  onPlatformChange,
}: ContentTypeSelectorProps) {
  return (
    <div className="flex gap-2">
      <Select value={contentType} onValueChange={onContentTypeChange}>
        <SelectTrigger className="w-[160px] bg-white/[0.04] border-white/[0.08] text-sm text-white hover:bg-white/[0.06] transition-colors">
          <SelectValue placeholder="Content Type" />
        </SelectTrigger>
        <SelectContent className="bg-[#0c2a3d] border-white/[0.08]">
          <SelectItem value="caption">Caption</SelectItem>
          <SelectItem value="carousel">Carousel Post</SelectItem>
          <SelectItem value="edm">EDM Copy</SelectItem>
          <SelectItem value="reel_script">Reel Script</SelectItem>
        </SelectContent>
      </Select>

      <Select value={platform} onValueChange={onPlatformChange}>
        <SelectTrigger className="w-[140px] bg-white/[0.04] border-white/[0.08] text-sm text-white hover:bg-white/[0.06] transition-colors">
          <SelectValue placeholder="Platform" />
        </SelectTrigger>
        <SelectContent className="bg-[#0c2a3d] border-white/[0.08]">
          <SelectItem value="instagram">Instagram</SelectItem>
          <SelectItem value="tiktok">TikTok</SelectItem>
          <SelectItem value="youtube">YouTube</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}

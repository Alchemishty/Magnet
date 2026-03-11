"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { TagInput } from "@/components/tag-input";
import {
  useGameProfile,
  useCreateGameProfile,
  useUpdateGameProfile,
} from "@/lib/hooks/use-game-profile";
import type { GameProfileCreate } from "@/lib/types/game-profile";

interface GameProfileFormProps {
  projectId: string;
}

export function GameProfileForm({ projectId }: GameProfileFormProps) {
  const { data: profile, isLoading, isError } = useGameProfile(projectId);
  const createProfile = useCreateGameProfile(projectId);
  const updateProfile = useUpdateGameProfile(projectId);
  const [jsonError, setJsonError] = useState("");

  const [form, setForm] = useState<GameProfileCreate>({
    genre: "",
    target_audience: "",
    core_mechanics: [],
    art_style: "",
    brand_guidelines: {},
    competitors: [],
    key_selling_points: [],
  });
  const [brandGuidelinesText, setBrandGuidelinesText] = useState("");

  useEffect(() => {
    if (profile) {
      setForm({
        genre: profile.genre || "",
        target_audience: profile.target_audience || "",
        core_mechanics: profile.core_mechanics || [],
        art_style: profile.art_style || "",
        brand_guidelines: profile.brand_guidelines || {},
        competitors: profile.competitors || [],
        key_selling_points: profile.key_selling_points || [],
      });
      setBrandGuidelinesText(
        profile.brand_guidelines
          ? JSON.stringify(profile.brand_guidelines, null, 2)
          : ""
      );
    } else if (!isLoading && !isError) {
      setForm({
        genre: "",
        target_audience: "",
        core_mechanics: [],
        art_style: "",
        brand_guidelines: {},
        competitors: [],
        key_selling_points: [],
      });
      setBrandGuidelinesText("");
    }
  }, [profile, isLoading, isError]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setJsonError("");
    let brandGuidelines: Record<string, unknown> = {};
    if (brandGuidelinesText.trim()) {
      try {
        const parsed = JSON.parse(brandGuidelinesText);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          setJsonError("Brand guidelines must be a JSON object.");
          return;
        }
        brandGuidelines = parsed;
      } catch {
        setJsonError("Invalid JSON in brand guidelines.");
        return;
      }
    }
    const data: GameProfileCreate = {
      ...form,
      brand_guidelines: brandGuidelines,
    };
    if (profile) {
      updateProfile.mutate(data);
    } else {
      createProfile.mutate(data);
    }
  };

  const isPending = createProfile.isPending || updateProfile.isPending;

  if (isLoading) {
    return <p className="text-muted-foreground">Loading game profile...</p>;
  }

  if (isError) {
    return <p className="text-destructive">Failed to load game profile.</p>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Game Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="genre">Genre</Label>
            <Input
              id="genre"
              value={form.genre || ""}
              onChange={(e) => setForm({ ...form, genre: e.target.value })}
              placeholder="e.g. Puzzle, RPG, Strategy"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="target-audience">Target Audience</Label>
            <Input
              id="target-audience"
              value={form.target_audience || ""}
              onChange={(e) =>
                setForm({ ...form, target_audience: e.target.value })
              }
              placeholder="e.g. Casual gamers 25-45"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="core-mechanics">Core Mechanics</Label>
            <TagInput
              id="core-mechanics"
              value={form.core_mechanics || []}
              onChange={(tags) => setForm({ ...form, core_mechanics: tags })}
              placeholder="Type and press Enter"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="art-style">Art Style</Label>
            <Input
              id="art-style"
              value={form.art_style || ""}
              onChange={(e) => setForm({ ...form, art_style: e.target.value })}
              placeholder="e.g. Cartoon, Realistic, Pixel art"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="brand-guidelines">Brand Guidelines (JSON)</Label>
            <Textarea
              id="brand-guidelines"
              value={brandGuidelinesText}
              onChange={(e) => setBrandGuidelinesText(e.target.value)}
              placeholder='{"primary_color": "#FF5733"}'
              rows={3}
            />
            {jsonError && (
              <p className="text-sm text-destructive">{jsonError}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="competitors">Competitors</Label>
            <TagInput
              id="competitors"
              value={form.competitors || []}
              onChange={(tags) => setForm({ ...form, competitors: tags })}
              placeholder="Type and press Enter"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="key-selling-points">Key Selling Points</Label>
            <TagInput
              id="key-selling-points"
              value={form.key_selling_points || []}
              onChange={(tags) =>
                setForm({ ...form, key_selling_points: tags })
              }
              placeholder="Type and press Enter"
            />
          </div>
          <Button type="submit" disabled={isPending}>
            {isPending
              ? "Saving..."
              : profile
                ? "Update Profile"
                : "Create Profile"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

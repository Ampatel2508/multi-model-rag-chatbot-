"use client";

import { useEffect, useState } from "react";
import { Check, ChevronDown, Cpu, Loader2, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { type Provider } from "@/lib/providers";

interface Model {
  id: string;
  name: string;
  description: string;
  context_window: number;
  max_output: number;
}

interface ModelSelectorProps {
  provider: Provider;
  apiKey: string;
  selectedModel: string;
  onModelChange: (model: string) => void;
}

export function ModelSelector({ provider, apiKey, selectedModel, onModelChange }: ModelSelectorProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const fetchModels = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch("/api/models", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider, apiKey }),
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("Failed to fetch models");
        }

        const data = await response.json();
        
        if (data.success && data.models) {
          setModels(data.models);
          // Auto-select first model if none selected
          if (!selectedModel && data.models.length > 0) {
            onModelChange(data.models[0].id);
          }
        } else {
          throw new Error("No models available");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load models");
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, [provider, apiKey, selectedModel, onModelChange]);

  const selectedModelName = models.find((m) => m.id === selectedModel)?.name || "Select a model";

  // Filter models based on search query
  const filteredModels = models.filter((model) =>
    model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    model.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <Button variant="outline" className="gap-2 min-w-50" disabled>
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Loading models...</span>
      </Button>
    );
  }

  if (error || models.length === 0) {
    return (
      <Button variant="outline" className="gap-2 min-w-50" disabled>
        <Cpu className="w-4 h-4" />
        <span>No models available</span>
      </Button>
    );
  }

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="gap-2 min-w-50 justify-between bg-transparent">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            <span className="truncate">{selectedModelName}</span>
          </div>
          <ChevronDown className="w-4 h-4 shrink-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-62.5 max-h-96 overflow-hidden p-0">
        {/* Search Bar */}
        <div className="sticky top-0 z-10 border-b bg-background p-2 space-y-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search models..."
              className="pl-8 h-8 text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          {filteredModels.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-2">
              No models found
            </p>
          ) : (
            <p className="text-xs text-muted-foreground px-1">
              {filteredModels.length} of {models.length} models
            </p>
          )}
        </div>

        {/* Models List */}
        <div className="overflow-y-auto max-h-80">
          {filteredModels.map((model) => (
            <DropdownMenuItem
              key={model.id}
              onClick={() => {
                onModelChange(model.id);
                setSearchQuery("");
                setIsOpen(false);
              }}
              className="flex items-center justify-between cursor-pointer px-4 py-2"
            >
              <div className="flex flex-col flex-1">
                <span className="font-medium text-sm">{model.name}</span>
                {model.description && (
                  <span className="text-xs text-muted-foreground truncate max-w-xs">
                    {model.description}
                  </span>
                )}
              </div>
              {selectedModel === model.id && <Check className="w-4 h-4 text-primary shrink-0 ml-2" />}
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
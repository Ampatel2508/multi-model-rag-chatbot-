import { useState } from "react";
import { Globe, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface URLInputProps {
  onUrlChange: (url: string) => void;
  url: string;
}

export function URLInput({ onUrlChange, url }: URLInputProps) {
  const [showInput, setShowInput] = useState(false);
  const [inputValue, setInputValue] = useState(url);

  const handleSubmit = () => {
    if (inputValue.trim()) {
      onUrlChange(inputValue.trim());
      setShowInput(false);
    }
  };

  const handleClear = () => {
    setInputValue("");
    onUrlChange("");
    setShowInput(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSubmit();
    } else if (e.key === "Escape") {
      setShowInput(false);
      setInputValue(url);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium mb-0">Documentation URL</label>
        {url && (
          <Button
            size="sm"
            variant="ghost"
            onClick={handleClear}
            className="h-6 w-6 p-0"
          >
            <X className="w-3 h-3" />
          </Button>
        )}
      </div>

      {url && !showInput ? (
        <div className="p-3 rounded-lg bg-muted text-sm break-all">
          <div className="flex items-start gap-2">
            <Globe className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="text-xs">{url}</span>
          </div>
        </div>
      ) : null}

      {showInput ? (
        <div className="space-y-2">
          <Input
            type="url"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="https://example.com/docs"
            className="text-sm"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={!inputValue.trim()}
              className="flex-1"
            >
              Add
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setShowInput(false);
                setInputValue(url);
              }}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowInput(true)}
          className="w-full gap-2"
        >
          <Globe className="w-4 h-4" />
          {url ? "Change URL" : "Add Documentation URL"}
        </Button>
      )}
    </div>
  );
}

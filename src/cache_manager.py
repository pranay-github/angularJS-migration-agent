import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class MigrationCache:
    def __init__(self, cache_dir: str = ".cache/migrations", ttl_days: int = 30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(days=ttl_days)
        self.hits = 0
        self.misses = 0
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except:
                return {}
        return {}
    
    def _save_index(self):
        self.index_file.write_text(json.dumps(self.index, indent=2))
    
    def _compute_hash(self, code: str, pattern_type: str, model: str) -> str:
        content = f"{code}|{pattern_type}|{model}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _is_expired(self, cache_entry: Dict) -> bool:
        if 'timestamp' not in cache_entry:
            return True
        
        cached_time = datetime.fromisoformat(cache_entry['timestamp'])
        return datetime.now() - cached_time > self.ttl
    
    def get(self, code: str, pattern_type: str, model: str) -> Optional[Dict[str, Any]]:
        cache_key = self._compute_hash(code, pattern_type, model)
        
        if cache_key in self.index:
            cache_entry = self.index[cache_key]
            
            if self._is_expired(cache_entry):
                del self.index[cache_key]
                self._save_index()
                self.misses += 1
                return None
            
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    cached_data = json.loads(cache_file.read_text())
                    self.hits += 1
                    print(f"   Cache HIT: {cache_key[:12]}... (saved LLM call)")
                    return cached_data
                except:
                    pass
        
        self.misses += 1
        return None
    
    def set(self, code: str, pattern_type: str, model: str, result: Dict[str, Any]):
        cache_key = self._compute_hash(code, pattern_type, model)
        
        cache_entry = {
            'timestamp': datetime.now().isoformat(),
            'pattern_type': pattern_type,
            'model': model,
            'code_size': len(code)
        }
        
        self.index[cache_key] = cache_entry
        self._save_index()
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_file.write_text(json.dumps(result, indent=2))
    
    def clear(self):
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.name != "index.json":
                cache_file.unlink()
        self.index = {}
        self._save_index()
        print(f" Cache cleared: {self.cache_dir}")
    
    def cleanup_expired(self):
        removed = 0
        for cache_key in list(self.index.keys()):
            if self._is_expired(self.index[cache_key]):
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    cache_file.unlink()
                del self.index[cache_key]
                removed += 1
        
        if removed > 0:
            self._save_index()
            print(f" Removed {removed} expired cache entries")
    
    def get_stats(self) -> Dict:
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'cache_hits': self.hits,
            'cache_misses': self.misses,
            'hit_rate': round(hit_rate, 1),
            'cached_entries': len(self.index),
            'cache_size_mb': self._get_cache_size_mb()
        }
    
    def _get_cache_size_mb(self) -> float:
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        return round(total_size / (1024 * 1024), 2)
    
    def format_stats(self) -> str:
        stats = self.get_stats()
        
        lines = []
        lines.append("=" * 70)
        lines.append(" CACHE STATISTICS")
        lines.append("=" * 70)
        lines.append(f"Total Requests:    {stats['total_requests']}")
        lines.append(f"Cache Hits:        {stats['cache_hits']} ({stats['hit_rate']}%)")
        lines.append(f"Cache Misses:      {stats['cache_misses']}")
        lines.append(f"Cached Entries:    {stats['cached_entries']}")
        lines.append(f"Cache Size:        {stats['cache_size_mb']} MB")
        lines.append("=" * 70)
        return "\n".join(lines)

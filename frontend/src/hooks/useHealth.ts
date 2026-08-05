import { useEffect, useRef, useState } from 'react';
import { getHealth } from '@/lib/api';

export type HealthState = 'online' | 'offline' | 'checking';

export function useHealth() {
  const [state, setState] = useState<HealthState>('checking');
  const [lastChecked, setLastChecked] = useState<number | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const check = async () => {
    try {
      await getHealth();
      setState('online');
      setLastChecked(Date.now());
    } catch {
      setState('offline');
      setLastChecked(Date.now());
    }
  };

  useEffect(() => {
    check();
    timer.current = setInterval(check, 30000);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  return { state, lastChecked, recheck: check };
}

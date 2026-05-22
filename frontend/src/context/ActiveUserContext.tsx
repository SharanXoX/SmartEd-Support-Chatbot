/**
 * Central active-user session for the mock LMS (multi-user simulation).
 * Re-exported as LmsStateContext for backward compatibility.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useLocation } from "react-router-dom";
import {
  buildLmsContextSnapshot,
  FALLBACK_ALEX,
  fetchStudentState,
  getActiveStudentId,
  listStudents,
  setActiveStudentId,
  type LmsContextSnapshot,
  type LmsStudentState,
  type StudentProfileOption,
} from "../services/mockApi";

export type ActiveUserContextValue = {
  state: LmsStudentState;
  loading: boolean;
  userProfiles: StudentProfileOption[];
  activeUserId: string;
  setActiveUser: (userId: string) => Promise<void>;
  refresh: () => Promise<void>;
  buildContextSnapshot: () => LmsContextSnapshot;
};

const ActiveUserContext = createContext<ActiveUserContextValue | null>(null);

const USER_CACHE_PREFIX = "smarted_user_cache:";

const PROFILE_LABELS: Record<string, { name: string; profile_type: string }> = {
  "alex-001": { name: "Alex", profile_type: "beginner" },
  "sam-001": { name: "Sam", profile_type: "overdue" },
  "priya-001": { name: "Priya", profile_type: "advanced" },
  "john-001": { name: "John", profile_type: "new" },
};

function readCachedUser(userId: string): LmsStudentState | null {
  try {
    const raw = sessionStorage.getItem(`${USER_CACHE_PREFIX}${userId}`);
    return raw ? (JSON.parse(raw) as LmsStudentState) : null;
  } catch {
    return null;
  }
}

function writeCachedUser(data: LmsStudentState): void {
  try {
    sessionStorage.setItem(`${USER_CACHE_PREFIX}${data.student_id}`, JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

function initialUserState(): LmsStudentState {
  const id = getActiveStudentId();
  return readCachedUser(id) ?? FALLBACK_ALEX;
}

export function ActiveUserProvider({ children }: { children: ReactNode }) {
  const location = useLocation();
  const [activeUserId, setActiveUserIdState] = useState(getActiveStudentId);
  const [state, setState] = useState<LmsStudentState>(initialUserState);
  const [loading, setLoading] = useState(false);
  const [userProfiles, setUserProfiles] = useState<StudentProfileOption[]>([]);

  const load = useCallback(async (userId: string) => {
    setLoading(true);
    try {
      const data = await fetchStudentState(userId);
      setState(data);
      writeCachedUser(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void listStudents().then(setUserProfiles);
  }, []);

  useEffect(() => {
    void load(activeUserId);
  }, [activeUserId, load]);

  const setActiveUser = useCallback(
    async (userId: string) => {
      const mapped = userId;
      setActiveStudentId(mapped);
      setActiveUserIdState(mapped);
      const cached = readCachedUser(mapped);
      if (cached) {
        setState(cached);
      } else {
        const profile = userProfiles.find((p) => p.id === mapped);
        const label = profile ?? PROFILE_LABELS[mapped];
        setState({
          ...FALLBACK_ALEX,
          student_id: mapped,
          name: label?.name ?? "Student",
          profile_type: label?.profile_type,
          courses: [],
          purchases: [],
          exams: [],
          certificates: [],
          recent_activity: [],
          announcements: mapped === "john-001" ? FALLBACK_ALEX.announcements : [],
        });
      }
      await load(mapped);
    },
    [load, userProfiles],
  );

  const buildContextSnapshot = useCallback(() => {
    return buildLmsContextSnapshot(state, location.pathname);
  }, [state, location.pathname]);

  const value = useMemo<ActiveUserContextValue>(
    () => ({
      state,
      loading,
      userProfiles,
      activeUserId,
      setActiveUser,
      refresh: () => load(activeUserId),
      buildContextSnapshot,
    }),
    [state, loading, userProfiles, activeUserId, setActiveUser, load, buildContextSnapshot],
  );

  return <ActiveUserContext.Provider value={value}>{children}</ActiveUserContext.Provider>;
}

export function useActiveUser() {
  const ctx = useContext(ActiveUserContext);
  if (!ctx) throw new Error("useActiveUser must be used within ActiveUserProvider");
  return ctx;
}

/** @deprecated Use useActiveUser — kept for existing imports */
export function useLmsState() {
  const ctx = useActiveUser();
  return {
    state: ctx.state,
    loading: ctx.loading,
    studentProfiles: ctx.userProfiles,
    activeStudentId: ctx.activeUserId,
    setActiveStudent: ctx.setActiveUser,
    refresh: ctx.refresh,
    buildContextSnapshot: ctx.buildContextSnapshot,
  };
}

/** @deprecated Use ActiveUserProvider */
export const LmsStateProvider = ActiveUserProvider;

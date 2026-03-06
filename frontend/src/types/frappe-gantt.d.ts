declare module 'frappe-gantt' {
  interface Task {
    id: string
    name: string
    start: string
    end: string
    progress?: number
    dependencies?: string
    custom_class?: string
    [key: string]: unknown
  }

  interface GanttOptions {
    view_mode?: string
    date_format?: string
    on_click?: (task: Task) => void
    on_date_change?: (task: Task, start: Date, end: Date) => void
    on_progress_change?: (task: Task, progress: number) => void
    on_view_change?: (mode: string) => void
    [key: string]: unknown
  }

  class Gantt {
    constructor(wrapper: string | HTMLElement, tasks: Task[], options?: GanttOptions)
    refresh(tasks: Task[]): void
    change_view_mode(mode: string): void
  }

  export default Gantt
}

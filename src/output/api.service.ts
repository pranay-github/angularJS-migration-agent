import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Application {
  id: string;
  params?: any;
}

export interface ApplicationComponent {
  id: string;
  name: string;
}

export interface ApplicationEnvironment {
  id: string;
  name: string;
  inactive?: boolean;
}

export interface ApplicationSnapshot {
  id: string;
  name: string;
  inactive?: boolean;
}

export interface ApplicationProcess {
  id: string;
  name: string;
  inactive?: boolean;
}

export interface TaskDefinition {
  id: string;
  name: string;
  active?: boolean;
}

export interface PagedResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
}

@Injectable({ providedIn: 'root' })
export class ApplicationService {
  private http = inject(HttpClient);
  private baseUrl = (window as any).bootstrap?.baseUrl || '';

  get(id: string): Observable<Application> {
    return this.http.get<Application>(`${this.baseUrl}rest/deploy/application/${id}`);
  }

  getE(id: string): Observable<Application[]> {
    return this.http.get<Application[]>(`${this.baseUrl}rest/deploy/application/${id}`);
  }

  save(application: Application): Observable<Application> {
    return this.http.put<Application>(`${this.baseUrl}rest/deploy/application`, application);
  }

  copyApplication(data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}rest/deploy/application/copyApplication`, data);
  }

  allPaged(params?: any): Observable<PagedResponse<Application>> {
    return this.http.get<PagedResponse<Application>>(`${this.baseUrl}rest/deploy/application/allPaged`, { params });
  }

  allPagedNew(params?: any): Observable<PagedResponse<Application>> {
    return this.http.get<PagedResponse<Application>>(`${this.baseUrl}rest/deploy/application/allPagedNew`, { params });
  }

  allForSelectPaged(params?: any): Observable<PagedResponse<Application>> {
    return this.http.get<PagedResponse<Application>>(`${this.baseUrl}rest/deploy/application/allForSelectPaged`, { params });
  }

  allForSelect(): Observable<Application[]> {
    return this.http.get<Application[]>(`${this.baseUrl}rest/deploy/application/allForSelect`);
  }

  all(): Observable<Application[]> {
    return this.http.get<Application[]>(`${this.baseUrl}rest/deploy/application`);
  }

  inactivate(id: string): Observable<any> {
    return this.http.put(`${this.baseUrl}rest/deploy/application/${id}/inactivate`, {});
  }

  activate(id: string): Observable<any> {
    return this.http.put(`${this.baseUrl}rest/deploy/application/${id}/activate`, {});
  }

  unusedEnvs(id: string): Observable<ApplicationEnvironment[]> {
    return this.http.get<ApplicationEnvironment[]>(`${this.baseUrl}rest/deploy/application/${id}/globalEnvironments/unused`);
  }

  usedEnvs(id: string): Observable<ApplicationEnvironment[]> {
    return this.http.get<ApplicationEnvironment[]>(`${this.baseUrl}rest/deploy/application/${id}/globalEnvironments/used`);
  }

  removeComponents(id: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}rest/deploy/application/${id}/removeComponents`, data);
  }

  processes(id: string, inactive: string): Observable<ApplicationProcess[]> {
    return this.http.get<ApplicationProcess[]>(`${this.baseUrl}rest/deploy/application/${id}/processes/${inactive}`);
  }

  fullProcesses(id: string): Observable<ApplicationProcess[]> {
    return this.http.get<ApplicationProcess[]>(`${this.baseUrl}rest/deploy/application/${id}/fullProcesses`);
  }

  components(id: string): Observable<ApplicationComponent[]> {
    return this.http.get<ApplicationComponent[]>(`${this.baseUrl}rest/deploy/application/${id}/components`);
  }

  componentsForSelect(id: string): Observable<ApplicationComponent[]> {
    return this.http.get<ApplicationComponent[]>(`${this.baseUrl}rest/deploy/application/${id}/componentsForSelect`);
  }

  componentTemplatesForSelect(id: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}rest/deploy/application/${id}/componentTemplatesForSelect`);
  }

  componentsPaged(id: string, params?: any): Observable<PagedResponse<ApplicationComponent>> {
    return this.http.get<PagedResponse<ApplicationComponent>>(`${this.baseUrl}rest/deploy/application/${id}/componentsPaged`, { params });
  }

  taskDefinitions(id: string, active: string): Observable<TaskDefinition[]> {
    return this.http.get<TaskDefinition[]>(`${this.baseUrl}rest/deploy/application/${id}/taskDefinitions/${active}`);
  }

  snapshots(id: string, inactive: string): Observable<ApplicationSnapshot[]> {
    return this.http.get<ApplicationSnapshot[]>(`${this.baseUrl}rest/deploy/application/${id}/snapshots/${inactive}`);
  }

  snapshotsPaged(id: string, params?: any): Observable<PagedResponse<ApplicationSnapshot>> {
    return this.http.get<PagedResponse<ApplicationSnapshot>>(`${this.baseUrl}rest/deploy/application/${id}/snapshotsPaged`, { params });
  }

  environments(id: string, inactive: string): Observable<ApplicationEnvironment[]> {
    return this.http.get<ApplicationEnvironment[]>(`${this.baseUrl}rest/deploy/application/${id}/environments/${inactive}`);
  }

  environmentsPaged(id: string, params?: any): Observable<PagedResponse<ApplicationEnvironment>> {
    return this.http.get<PagedResponse<ApplicationEnvironment>>(`${this.baseUrl}rest/deploy/application/${id}/environmentsPaged`, { params });
  }

  executableProcessesPaged(id: string, params?: any): Observable<PagedResponse<ApplicationProcess>> {
    return this.http.get<PagedResponse<ApplicationProcess>>(`${this.baseUrl}rest/deploy/application/${id}/executableProcessesPaged`, { params });
  }

  snapshotsForEnvironment(appId: string, envId: string, inactive: string): Observable<ApplicationSnapshot[]> {
    return this.http.get<ApplicationSnapshot[]>(`${this.baseUrl}rest/deploy/application/${appId}/${envId}/snapshotsForEnvironment/${inactive}`);
  }

  runProcess(id: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}rest/deploy/application/${id}/runProcess`, data);
  }

  processesPaged(id: string, params?: any): Observable<PagedResponse<ApplicationProcess>> {
    return this.http.get<PagedResponse<ApplicationProcess>>(`${this.baseUrl}rest/deploy/application/${id}/processesPaged`, { params });
  }

  taskDefinitionsPaged(id: string, params?: any): Observable<PagedResponse<TaskDefinition>> {
    return this.http.get<PagedResponse<TaskDefinition>>(`${this.baseUrl}rest/deploy/application/${id}/taskDefinitionsPaged`, { params });
  }

  pasteProcess(id: string, proc: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}rest/deploy/application/${id}/pasteProcess/${proc}`, data);
  }

  processDeployments(id: string): Observable<any> {
    return this.http.get(`${this.baseUrl}rest/deploy/application/${id}/processDeployments`);
  }

  latestDesiredInventories(id: string): Observable<any> {
    return this.http.get(`${this.baseUrl}rest/deploy/application/${id}/latestDesiredInventories`);
  }

  orderEnvironments(id: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}rest/deploy/application/${id}/orderEnvironments`, data);
  }

  unusedComponents(id: string): Observable<ApplicationComponent[]> {
    return this.http.get<ApplicationComponent[]>(`${this.baseUrl}rest/deploy/application/${id}/unusedComponents`);
  }

  unusedComponentsPaged(id: string, params?: any): Observable<PagedResponse<ApplicationComponent>> {
    return this.http.get<PagedResponse<ApplicationComponent>>(`${this.baseUrl}rest/deploy/application/${id}/unusedComponentsPaged`, { params });
  }

  addComponents(id: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}rest/deploy/application/${id}/addComponents`, data);
  }

  basicDeploySummary(id: string): Observable<any> {
    return this.http.get(`${this.baseUrl}rest/deploy/application/${id}/basicDeploySummary`);
  }

  lastAndNextDeployments(id: string): Observable<any> {
    return this.http.get(`${this.baseUrl}rest/deploy/application/${id}/lastAndNextDeployments`);
  }

  environmentsWithResourceInfo(id: string): Observable<ApplicationEnvironment[]> {
    return this.http.get<ApplicationEnvironment[]>(`${this.baseUrl}rest/deploy/application/${id}/environmentsWithResourceInfo`);
  }

  processesForComponent(id: string): Observable<ApplicationProcess[]> {
    return this.http.get<ApplicationProcess[]>(`${this.baseUrl}rest/deploy/application/processes/forComponent/${id}`);
  }

  environmentsForComponent(id: string): Observable<ApplicationEnvironment[]> {
    return this.http.get<ApplicationEnvironment[]>(`${this.baseUrl}rest/deploy/application/environments/forComponent/${id}`);
  }

  allForConditions(data: any): Observable<Application[]> {
    const headers = new HttpHeaders({
      'da-force-read-only-request': 'true'
    });
    return this.http.post<Application[]>(`${this.baseUrl}rest/deploy/application/allForConditions`, data, { headers });
  }
}
/*
 * Copyright 2012–2025 Open Text.
 *
 * The only warranties for products and services of Open Text and its affiliates and licensors ("Open Text") are as may be set forth in the express warranty statements accompanying such products and services. Nothing herein should be construed as constituting an additional warranty. Open Text shall not be liable for technical or editorial errors or omissions contained herein. The information contained herein is subject to change without notice.
 *
 * Except as specifically indicated otherwise, this document contains confidential information and a valid license is required for possession, use or copying. If this work is provided to the U.S. Government, consistent with FAR 12.211 and 12.212, Commercial Computer Software, Computer Software Documentation, and Technical Data for Commercial Items are licensed to the U.S. Government under vendor's standard commercial license.
 */

export default ["$resource", "$bootstrap",
    function($resource, $bootstrap) {

        return $resource(
            $bootstrap.baseUrl,
            {
                id: "@id",
                params: "@params"
            },
            {
                get: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id"
                },
                getE: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id",
                    isArray: true
                },
                save: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application"
                },
                copyApplication: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application/copyApplication"
                },
                allPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/allPaged"
                },
                allPagedNew: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/allPagedNew"
                },
                allForSelectPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/allForSelectPaged"
                },
                allForSelect: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/allForSelect",
                    isArray: true
                },
                all: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application",
                    isArray: true
                },
                inactivate: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/inactivate"
                },
                activate: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/activate"
                },
                unusedEnvs: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/globalEnvironments/unused",
                    isArray: true
                },
                usedEnvs: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/globalEnvironments/used",
                    isArray: true
                },
                removeComponents: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/removeComponents"
                },
                processes: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/processes/:inactive",
                    isArray: true
                },
                fullProcesses: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/fullProcesses",
                    isArray: true
                },
                components: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/components",
                    isArray: true
                },
                componentsForSelect: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/componentsForSelect",
                    isArray: true
                },
                componentTemplatesForSelect: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/componentTemplatesForSelect",
                    isArray: true
                },
                componentsPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/componentsPaged"
                },
                taskDefinitions: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/taskDefinitions/:active",
                    isArray: true
                },
                snapshots: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/snapshots/:inactive",
                    isArray: true
                },
                snapshotsPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/snapshotsPaged"
                },
                environments: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/environments/:inactive",
                    isArray: true
                },
                environmentsPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/environmentsPaged"
                },
                executableProcessesPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/executableProcessesPaged"
                },
                snapshotsForEnvironment: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:appId/:envId/snapshotsForEnvironment/:inactive",
                    isArray: true
                },
                runProcess: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/runProcess"
                },
                processesPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/processesPaged"
                },
                taskDefinitionsPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/taskDefinitionsPaged"
                },
                pasteProcess: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/pasteProcess/:proc"
                },
                processDeployments: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/processDeployments"
                },
                latestDesiredInventories: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/latestDesiredInventories"
                },
                orderEnvironments: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/orderEnvironments"
                },
                unusedComponents: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/unusedComponents",
                    isArray: true
                },
                unusedComponentsPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/unusedComponentsPaged"
                },
                addComponents: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/addComponents"
                },
                basicDeploySummary: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/basicDeploySummary"
                },
                lastAndNextDeployments: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/lastAndNextDeployments"
                },
                environmentsWithResourceInfo: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/:id/environmentsWithResourceInfo",
                    isArray: true
                },
                processesForComponent: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/processes/forComponent/:id",
                    isArray: true
                },
                environmentsForComponent: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/deploy/application/environments/forComponent/:id",
                    isArray: true
                },
                allForConditions: {
                    method: "POST",
                    headers: {
                        'da-force-read-only-request': true
                    },
                    url: $bootstrap.baseUrl + "rest/deploy/application/allForConditions"
                },
            }
        );
    }
]
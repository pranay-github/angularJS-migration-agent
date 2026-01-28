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
                allPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/allPaged"
                },
                inactivate: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/:id/inactivate"
                },
                activate: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/:id/activate"
                },
                delete: {
                    method: "DELETE",
                    url: $bootstrap.baseUrl + "rest/agent/:id"
                },
                upgrade :{
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/:id/upgrade"
                },
                upgradeSelected: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/upgrade"
                },
                restart: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/:id/restart"
                },
                all: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/:inactive",
                    isArray: true
                },
                sshInstallAgent: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/sshInstallAgent"
                },
                get: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/:id"
                },
                save: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent"
                },
                runConnectivityTest: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/:id/connectivity"
                },
                resourcesPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/:id/resourcesPaged"
                },
                poolsPaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/:id/poolsPaged"
                },
                assignableToLicense: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/assignableToLicense/:licenseId",
                    isArray: true
                },
                assignableToLicensePaged: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/assignableToLicensePaged/:licenseId"
                },
                assignAgentsToLicense: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/assignAgentsToLicense/:licenseId"
                },
                resolvedName: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/:id/resolvedName",
                    isArray: false
                },
                searchProperties: {
                    method: "GET",
                    url: $bootstrap.baseUrl + "rest/agent/searchProperties/:id",
                    isArray: true
                },
                supportedJREs: {
                    method: "POST",
                    url: $bootstrap.baseUrl + "rest/agent/supportedJREs",
                    isArray: true
                },
                updateJreOnAgents: {
                    method: "PUT",
                    url: $bootstrap.baseUrl + "rest/agent/updateJreOnAgents"
                },
                validateUpgrade: {
                    method: "POST",
                    url: $bootstrap.baseUrl + "rest/agent/validateUpgrade",
                    isArray: true
                }
            }
        );
    }
]
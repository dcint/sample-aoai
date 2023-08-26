import { UserInfo, ConversationRequest } from "./models";


export async function conversationApi(options: ConversationRequest, abortSignal: AbortSignal): Promise<Response> {

    const accessToken = await getUserToken();
    // const oaiToken = await getOaiToken();
    // console.log(`Access Token: ${oaiToken}`);

    const UserID = await extractUPN();
    console.log(`User ID: ${UserID}`);

    const response = await fetch("/conversation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Cache-Control": "max-age=3600",
            "Authorization": `Bearer ${accessToken}`,
            "User-Id": `${UserID}`
        },

        body: JSON.stringify({
            messages: options.messages
        }),
        signal: abortSignal
    });

    return response;
}

export async function getUserInfo(): Promise<UserInfo[]> {
    const response = await fetch('/.auth/me');
    if (!response.ok) {
        console.log("No identity provider found. Access to chat will be blocked.")
        return [];
    }

    const payload = await response.json();
    return payload;
}

import jwt_decode from 'jwt-decode';

export async function extractUPN() {
    const accessToken = await getUserToken();
    const decodedToken = jwt_decode(accessToken) as { unique_name: string };
    const upn = decodedToken.unique_name;
    return upn;
}

export async function getUserToken(): Promise<string> {
    const response = await fetch('/.auth/me');
    if (!response.ok) {
        console.log("No identity provider found. Access to chat will be blocked.")
        return "";
    }
    const payload = await response.json();
    const userInfo = payload[0];
    if (!userInfo) {
        console.log("No user information found. Access to chat will be blocked.")
        return "";
    }
    const tokenExpired = userInfo.expires_on;
    if (!tokenExpired) {
        console.log("No token expiration information found. Access to chat will be blocked.")
    }
    console.log(`Token expiration: ${tokenExpired}`);

    const tokenExpirationTime = tokenExpired;
    console.log(`Token expiration time: ${tokenExpirationTime}`);


    const refreshEndpoint = ('/.auth/refresh');

    console.log(`Refresh endpoint: ${refreshEndpoint}`);
    const expirationTime = new Date(tokenExpirationTime);
    console.log(`Token expiration time: ${expirationTime}`);
    const currentTime = new Date();
    console.log(`Current time: ${currentTime}`);
    const timeDifference = expirationTime.getTime() - currentTime.getTime();
    console.log(`Time difference: ${timeDifference}`);
    if (timeDifference <= 0 || timeDifference <= 5 * 60 * 1000) {
        try {
            const refreshResponse = await fetch(refreshEndpoint);
            if (!refreshResponse.ok) {
                throw new Error('Refresh request failed');
            }
            console.log('Refresh successful:', refreshResponse.status);
            const refreshedPayload = await fetch('/.auth/me').then(res => res.json());
            const refreshedUserInfo = refreshedPayload[0];
            const refreshedAccessToken = refreshedUserInfo.access_token;
            if (!refreshedAccessToken) {
                console.log("No refreshed access token found. Access to chat will be blocked.")
                return "";
            }
            return refreshedAccessToken;
        } catch (error) {
            console.error('Refresh failed:', error);
            return "";
        }
    } else {
        const accessToken = userInfo.access_token;
        if (!accessToken) {
            console.log("No access token found. Access to chat will be blocked.")
            return "";
        }
        return accessToken;
    }
}

// export async function getOaiToken() {
//     const response = await fetch('https://cognitiveservices.azure.com/.default');
//     if (!response.ok) {
//         console.log("No AAD AI provider found. Access to chat will be blocked.")
//         return "";
//     }
//     const payload = await response.json();
//     const Token = payload[0];
//     console.log(`Token: ${Token}`);
//     return Token;
// }


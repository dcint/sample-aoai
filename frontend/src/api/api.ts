import { UserInfo, ConversationRequest } from "./models";


export async function conversationApi(options: ConversationRequest, abortSignal: AbortSignal): Promise<Response> {

    const accessToken = await getUserToken();
    const principal = await getUserInfo_with_principal();
    console.log(`Principal: ${principal}`);

    // const userId = await getUserId();
    const response = await fetch("/conversation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Cache-Control": "max-age=3600",
            "Authorization": `Bearer ${accessToken}`
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

export async function getUserInfo_with_principal() {
    const response = await fetch('/.auth/me');
    const payload = await response.json();
    const { clientPrincipal } = payload;
    return clientPrincipal;
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
//     if (timeDifference <= 0 || timeDifference <= 5 * 60 * 1000) {
//         fetch(refreshEndpoint)
//             .then(response => {
//                 if (!response.ok) {
//                     throw new Error('Refresh request failed');
//                 }
//                 console.log('Refresh successful:', response.status);
//             })

//             .catch(error => {
//                 console.error('Refresh failed:', error);

//             });

//     } else {
//         const accessToken = userInfo.access_token;
//         if (!accessToken) {
//             console.log("No access token found. Access to chat will be blocked.")
//             return "";
//         }
//         return accessToken;
//     }
//     return userInfo.access_token || "";
// }

// async function getUserId() {
//     const response = await fetch('/.auth/me');
//     if (!response.ok) {
//         throw new Error(`Failed to get user info: ${response.status} ${response.statusText}`);
//     }
//     const payload = await response.json();
//     const userInfo = payload[0];
//     if (!userInfo) {
//         throw new Error('No user info found');
//     }
//     const userId = atob(userInfo.user_id);
//     return userId;
// }
//             .catch(error => {
//                 console.error('Refresh failed:', error);

//             });

//     } else {
//         const accessToken = userInfo.access_token;
//         if (!accessToken) {
//             console.log("No access token found. Access to chat will be blocked.")
//             return "";
//         }
//         return accessToken;
//     }
//     return "";
// }
//     const accessToken = userInfo.access_token;
//     if (!accessToken) {
//         console.log("No access token found. Access to chat will be blocked.")
//         return "";
//     }
//     return accessToken;
// }

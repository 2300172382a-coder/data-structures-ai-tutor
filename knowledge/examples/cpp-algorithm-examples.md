# C++ 示例代码与复杂度说明

## 单链表原地逆置

```cpp
struct Node { int value; Node* next; };

Node* reverse(Node* head) {
    Node* prev = nullptr;
    Node* cur = head;
    while (cur != nullptr) {
        Node* next = cur->next;
        cur->next = prev;
        prev = cur;
        cur = next;
    }
    return prev;
}
```

每个结点访问一次，时间 `O(n)`，额外空间 `O(1)`。关键点是在改变 `cur->next` 前保存原后继。

## 广度优先搜索

```cpp
vector<int> bfs(const vector<vector<int>>& graph, int start) {
    if (start < 0 || start >= static_cast<int>(graph.size())) return {};
    vector<bool> visited(graph.size(), false);
    queue<int> pending;
    vector<int> order;
    visited[start] = true;
    pending.push(start);
    while (!pending.empty()) {
        int u = pending.front(); pending.pop();
        order.push_back(u);
        for (int v : graph[u]) {
            if (!visited[v]) {
                visited[v] = true;
                pending.push(v);
            }
        }
    }
    return order;
}
```

应在入队时标记访问，而不是出队时标记，否则同一顶点可能重复入队。邻接表上时间 `O(|V|+|E|)`，空间 `O(|V|)`。

## 归并两个有序区间

```cpp
void merge_range(vector<int>& a, int left, int mid, int right) {
    vector<int> temp;
    temp.reserve(right - left + 1);
    int i = left, j = mid + 1;
    while (i <= mid && j <= right) {
        if (a[i] <= a[j]) temp.push_back(a[i++]);
        else temp.push_back(a[j++]);
    }
    while (i <= mid) temp.push_back(a[i++]);
    while (j <= right) temp.push_back(a[j++]);
    for (int k = 0; k < static_cast<int>(temp.size()); ++k)
        a[left + k] = temp[k];
}
```

比较时使用 `<=`，让左区间中的相等元素先进入结果，从而保持稳定性。合并时间 `O(right-left+1)`，辅助空间同阶。

[资料类型：示例代码；语言：C++]

